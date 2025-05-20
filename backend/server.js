const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const morgan = require('morgan');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Initialize express app
const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(morgan('dev'));

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy' });
});

// Database setup
const dbPath = path.resolve(__dirname, 'data', 'iot_dashboard.db');
const db = new sqlite3.Database(dbPath);

// Create tables if they don't exist
db.serialize(() => {
  db.run(`
    CREATE TABLE IF NOT EXISTS weeks (
      id TEXT PRIMARY KEY,
      start_date TEXT NOT NULL,
      end_date TEXT NOT NULL,
      data_type TEXT NOT NULL,
      created_at INTEGER NOT NULL,
      last_modified INTEGER NOT NULL
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS iot_data (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      week_id TEXT NOT NULL,
      time TEXT NOT NULL,
      data JSON NOT NULL,
      FOREIGN KEY (week_id) REFERENCES weeks (id)
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS manual_corrections (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      week_id TEXT NOT NULL,
      pump_duration REAL,
      total_flow_ara REAL,
      total_flow_galgenkanal REAL,
      notes TEXT,
      FOREIGN KEY (week_id) REFERENCES weeks (id)
    )
  `);
});

// Helper function to generate week ID
const generateWeekId = (startDate, endDate) => {
  return `week_${startDate.replace(/\//g, '-')}_to_${endDate.replace(/\//g, '-')}`;
};

// API Routes

// Get all weeks
app.get('/api/weeks', (req, res) => {
  db.all('SELECT * FROM weeks ORDER BY created_at DESC', (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(rows);
  });
});

// Get a specific week with its data and corrections
app.get('/api/weeks/:id', (req, res) => {
  const weekId = req.params.id;
  
  // Get week info
  db.get('SELECT * FROM weeks WHERE id = ?', [weekId], (err, week) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    if (!week) {
      return res.status(404).json({ error: 'Week not found' });
    }
    
    // Get IoT data for the week
    db.all('SELECT * FROM iot_data WHERE week_id = ?', [weekId], (err, iotData) => {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      
      // Parse JSON data
      const parsedIotData = iotData.map(item => {
        return {
          ...item,
          data: JSON.parse(item.data)
        };
      });
      
      // Get manual corrections for the week
      db.all('SELECT * FROM manual_corrections WHERE week_id = ?', [weekId], (err, corrections) => {
        if (err) {
          return res.status(500).json({ error: err.message });
        }
        
        // Combine all data
        const result = {
          ...week,
          iotData: parsedIotData.map(item => item.data),
          manualCorrections: corrections
        };
        
        res.json(result);
      });
    });
  });
});

// Create a new week
app.post('/api/weeks', (req, res) => {
  const { startDate, endDate, dataType, iotData, manualCorrections = [] } = req.body;
  
  if (!startDate || !endDate || !dataType || !iotData) {
    return res.status(400).json({ error: 'Missing required fields' });
  }
  
  const weekId = generateWeekId(startDate, endDate);
  const now = Date.now();
  
  // Begin transaction
  db.serialize(() => {
    db.run('BEGIN TRANSACTION');
    
    // Insert week
    db.run(
      'INSERT INTO weeks (id, start_date, end_date, data_type, created_at, last_modified) VALUES (?, ?, ?, ?, ?, ?)',
      [weekId, startDate, endDate, dataType, now, now],
      function(err) {
        if (err) {
          db.run('ROLLBACK');
          return res.status(500).json({ error: err.message });
        }
        
        // Insert IoT data
        const iotStmt = db.prepare('INSERT INTO iot_data (week_id, time, data) VALUES (?, ?, ?)');
        
        for (const item of iotData) {
          const time = item.Time || '';
          iotStmt.run(weekId, time, JSON.stringify(item));
        }
        
        iotStmt.finalize();
        
        // Insert manual corrections if any
        if (manualCorrections.length > 0) {
          const corrStmt = db.prepare(
            'INSERT INTO manual_corrections (week_id, pump_duration, total_flow_ara, total_flow_galgenkanal, notes) VALUES (?, ?, ?, ?, ?)'
          );
          
          for (const corr of manualCorrections) {
            corrStmt.run(
              weekId,
              corr.pumpDuration || 0,
              corr.totalFlowARA || 0,
              corr.totalFlowGalgenkanal || 0,
              corr.notes || ''
            );
          }
          
          corrStmt.finalize();
        }
        
        db.run('COMMIT', function(err) {
          if (err) {
            db.run('ROLLBACK');
            return res.status(500).json({ error: err.message });
          }
          
          res.status(201).json({ id: weekId, message: 'Week created successfully' });
        });
      }
    );
  });
});

// Update a week
app.put('/api/weeks/:id', (req, res) => {
  const weekId = req.params.id;
  const { dataType } = req.body;
  const now = Date.now();
  
  if (!dataType) {
    return res.status(400).json({ error: 'Missing required fields' });
  }
  
  db.run(
    'UPDATE weeks SET data_type = ?, last_modified = ? WHERE id = ?',
    [dataType, now, weekId],
    function(err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      
      if (this.changes === 0) {
        return res.status(404).json({ error: 'Week not found' });
      }
      
      res.json({ message: 'Week updated successfully' });
    }
  );
});

// Delete a week
app.delete('/api/weeks/:id', (req, res) => {
  const weekId = req.params.id;
  
  db.serialize(() => {
    db.run('BEGIN TRANSACTION');
    
    // Delete manual corrections
    db.run('DELETE FROM manual_corrections WHERE week_id = ?', [weekId]);
    
    // Delete IoT data
    db.run('DELETE FROM iot_data WHERE week_id = ?', [weekId]);
    
    // Delete week
    db.run('DELETE FROM weeks WHERE id = ?', [weekId], function(err) {
      if (err) {
        db.run('ROLLBACK');
        return res.status(500).json({ error: err.message });
      }
      
      if (this.changes === 0) {
        db.run('ROLLBACK');
        return res.status(404).json({ error: 'Week not found' });
      }
      
      db.run('COMMIT', function(err) {
        if (err) {
          db.run('ROLLBACK');
          return res.status(500).json({ error: err.message });
        }
        
        res.json({ message: 'Week deleted successfully' });
      });
    });
  });
});

// Add manual correction to a week
app.post('/api/weeks/:id/corrections', (req, res) => {
  const weekId = req.params.id;
  const { pumpDuration, totalFlowARA, totalFlowGalgenkanal, notes } = req.body;
  
  // Check if week exists
  db.get('SELECT id FROM weeks WHERE id = ?', [weekId], (err, row) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    
    if (!row) {
      return res.status(404).json({ error: 'Week not found' });
    }
    
    // Insert correction
    db.run(
      'INSERT INTO manual_corrections (week_id, pump_duration, total_flow_ara, total_flow_galgenkanal, notes) VALUES (?, ?, ?, ?, ?)',
      [weekId, pumpDuration || 0, totalFlowARA || 0, totalFlowGalgenkanal || 0, notes || ''],
      function(err) {
        if (err) {
          return res.status(500).json({ error: err.message });
        }
        
        // Update week's last_modified
        db.run('UPDATE weeks SET last_modified = ? WHERE id = ?', [Date.now(), weekId]);
        
        res.status(201).json({ 
          id: this.lastID,
          message: 'Correction added successfully' 
        });
      }
    );
  });
});

// Update a manual correction
app.put('/api/weeks/:id/corrections/:correctionId', (req, res) => {
  const weekId = req.params.id;
  const correctionId = req.params.correctionId;
  const { pumpDuration, totalFlowARA, totalFlowGalgenkanal, notes } = req.body;
  
  db.run(
    'UPDATE manual_corrections SET pump_duration = ?, total_flow_ara = ?, total_flow_galgenkanal = ?, notes = ? WHERE id = ? AND week_id = ?',
    [pumpDuration || 0, totalFlowARA || 0, totalFlowGalgenkanal || 0, notes || '', correctionId, weekId],
    function(err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      
      if (this.changes === 0) {
        return res.status(404).json({ error: 'Correction not found' });
      }
      
      // Update week's last_modified
      db.run('UPDATE weeks SET last_modified = ? WHERE id = ?', [Date.now(), weekId]);
      
      res.json({ message: 'Correction updated successfully' });
    }
  );
});

// Delete a manual correction
app.delete('/api/weeks/:id/corrections/:correctionId', (req, res) => {
  const weekId = req.params.id;
  const correctionId = req.params.correctionId;
  
  db.run(
    'DELETE FROM manual_corrections WHERE id = ? AND week_id = ?',
    [correctionId, weekId],
    function(err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      
      if (this.changes === 0) {
        return res.status(404).json({ error: 'Correction not found' });
      }
      
      // Update week's last_modified
      db.run('UPDATE weeks SET last_modified = ? WHERE id = ?', [Date.now(), weekId]);
      
      res.json({ message: 'Correction deleted successfully' });
    }
  );
});

// Data cleanup - delete data older than 1 year
const cleanupOldData = () => {
  const oneYearAgo = new Date();
  oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
  const timestamp = oneYearAgo.getTime();
  
  db.all('SELECT id FROM weeks WHERE created_at < ?', [timestamp], (err, rows) => {
    if (err || !rows.length) return;
    
    db.serialize(() => {
      db.run('BEGIN TRANSACTION');
      
      rows.forEach(row => {
        const weekId = row.id;
        
        // Delete manual corrections
        db.run('DELETE FROM manual_corrections WHERE week_id = ?', [weekId]);
        
        // Delete IoT data
        db.run('DELETE FROM iot_data WHERE week_id = ?', [weekId]);
        
        // Delete week
        db.run('DELETE FROM weeks WHERE id = ?', [weekId]);
      });
      
      db.run('COMMIT');
    });
  });
};

// Run cleanup once a day
setInterval(cleanupOldData, 24 * 60 * 60 * 1000);

// Create data directory if it doesn't exist
const fs = require('fs');
const dataDir = path.resolve(__dirname, 'data');
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir);
}

// Start server
app.listen(port, '0.0.0.0', () => {
  console.log(`Server running on port ${port}`);
});

// Handle graceful shutdown
process.on('SIGINT', () => {
  db.close();
  process.exit(0);
});
