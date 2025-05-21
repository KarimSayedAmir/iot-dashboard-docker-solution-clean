const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const morgan = require('morgan');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const csv = require('csv-parse');
const fs = require('fs');
const multer = require('multer');

// Configure multer for file upload
const upload = multer({ dest: 'uploads/' });

// Initialize express app
const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(morgan('dev'));

// API Prefix-Handling Middleware - Damit URLs sowohl mit als auch ohne /api-Präfix funktionieren
app.use((req, res, next) => {
  // Health-Endpunkt direkt weitergeben
  if (req.path === '/health') {
    return next();
  }

  // Überprüfen, ob die URL mit /api beginnt
  const apiPrefixRegex = /^\/api\//;
  if (!apiPrefixRegex.test(req.originalUrl)) {
    // Wenn die URL nicht mit /api beginnt, prüfen, ob eine entsprechende Route existiert
    // Aktuell sind alle Routen mit /api definiert
    const apiUrl = `/api${req.originalUrl}`;
    console.log(`Redirecting ${req.originalUrl} to ${apiUrl}`);
    req.originalUrl = apiUrl;
    req.url = apiUrl;
  }
  next();
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy' });
});

// API health check endpoint
app.get('/api/health', (req, res) => {
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

// Helper function to parse CSV data
const parseCSVFile = (filePath) => {
  return new Promise((resolve, reject) => {
    const results = [];
    const headerData = {};

    fs.createReadStream(filePath)
      .pipe(csv({
        skip_empty_lines: true,
        from_line: 1
      }))
      .on('data', (data) => {
        // First 5 lines contain header information
        if (results.length < 5) {
          const [key, value] = data;
          headerData[key] = value;
        } else if (results.length === 5) {
          // This is the column headers line
          headerData.columns = data;
        } else {
          // These are the actual data rows
          const row = {};
          headerData.columns.forEach((col, index) => {
            row[col] = data[index];
          });
          results.push(row);
        }
      })
      .on('end', () => {
        resolve({
          headerInfo: headerData,
          data: results
        });
      })
      .on('error', reject);
  });
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
const dataDir = path.resolve(__dirname, 'data');
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir);
}

// Make sure uploads directory exists
const uploadsDir = path.resolve(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir);
}

// Hilfsfunktion für CSV-Upload-Verarbeitung
const handleCsvUpload = async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }

  try {
    const parsedData = await parseCSVFile(req.file.path);
    
    // Extract date range from header info
    const startDate = parsedData.headerInfo['Start Time'];
    const endDate = parsedData.headerInfo['End Time'];
    const customer = parsedData.headerInfo['Customer'];
    const name = parsedData.headerInfo['Name'];
    
    // Generate week ID using the actual dates from the file
    const weekId = `week_${startDate.replace(/[\s:]/g, '-')}_to_${endDate.replace(/[\s:]/g, '-')}`;
    const now = Date.now();

    // Begin transaction
    db.serialize(() => {
      db.run('BEGIN TRANSACTION');

      // Insert week with actual dates from file
      db.run(
        'INSERT INTO weeks (id, start_date, end_date, data_type, created_at, last_modified) VALUES (?, ?, ?, ?, ?, ?)',
        [weekId, startDate, endDate, 'telemetry', now, now],
        function(err) {
          if (err) {
            db.run('ROLLBACK');
            return res.status(500).json({ error: err.message });
          }

          // Insert IoT data
          const iotStmt = db.prepare('INSERT INTO iot_data (week_id, time, data) VALUES (?, ?, ?)');

          // Remove duplicate entries (same timestamp)
          const uniqueData = parsedData.data.reduce((acc, current) => {
            const exists = acc.find(item => item.Time === current.Time);
            if (!exists) {
              acc.push(current);
            }
            return acc;
          }, []);

          for (const item of uniqueData) {
            iotStmt.run(weekId, item.Time, JSON.stringify(item));
          }

          iotStmt.finalize();

          db.run('COMMIT', function(err) {
            if (err) {
              db.run('ROLLBACK');
              return res.status(500).json({ error: err.message });
            }

            // Clean up uploaded file
            fs.unlink(req.file.path, (err) => {
              if (err) console.error('Error deleting file:', err);
            });

            res.status(201).json({
              id: weekId,
              message: 'CSV data imported successfully',
              summary: {
                customer,
                name,
                startDate,
                endDate,
                recordCount: uniqueData.length,
                originalRecordCount: parsedData.data.length,
                duplicatesRemoved: parsedData.data.length - uniqueData.length
              }
            });
          });
        }
      );
    });
  } catch (error) {
    // Clean up uploaded file
    fs.unlink(req.file.path, (err) => {
      if (err) console.error('Error deleting file:', err);
    });
    
    res.status(500).json({ error: error.message });
  }
};

// New route to handle CSV file upload with /api prefix
app.post('/api/upload-csv', upload.single('file'), handleCsvUpload);

// Alternative route without /api prefix
app.post('/upload-csv', upload.single('file'), handleCsvUpload);

// Start server
app.listen(port, '0.0.0.0', () => {
  console.log(`Server running on port ${port}`);
});

// Handle graceful shutdown
process.on('SIGINT', () => {
  db.close();
  process.exit(0);
});
