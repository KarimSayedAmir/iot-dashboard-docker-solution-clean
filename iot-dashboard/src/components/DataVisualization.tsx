import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { IoTData, ChartConfig } from '../types';

interface DataVisualizationProps {
  data: IoTData[];
  config: ChartConfig;
}

const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', 
  '#00C49F', '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57'
];

const DataVisualization: React.FC<DataVisualizationProps> = ({ data, config }) => {
  const [chartData, setChartData] = useState<any[]>([]);

  useEffect(() => {
    // Formatiere die Daten für das Diagramm
    const formattedData = data.map(item => {
      const formattedItem: any = {
        time: item.Time,
      };
      
      config.variables.forEach(variable => {
        formattedItem[variable] = item[variable];
      });
      
      return formattedItem;
    });
    
    setChartData(formattedData);
  }, [data, config.variables]);

  const renderChart = () => {
    if (config.type === 'line') {
      return (
        <ResponsiveContainer width="100%" height={400}>
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis label={{ value: config.yAxisLabel, angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            {config.variables.map((variable, index) => (
              <Line 
                key={variable}
                type="monotone"
                dataKey={variable}
                stroke={COLORS[index % COLORS.length]}
                activeDot={{ r: 8 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      );
    } else if (config.type === 'bar') {
      return (
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis label={{ value: config.yAxisLabel, angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            {config.variables.map((variable, index) => (
              <Bar 
                key={variable}
                dataKey={variable}
                fill={COLORS[index % COLORS.length]}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      );
    }
    
    return null;
  };

  return (
    <div className="chart-container">
      <h2>{config.title}</h2>
      {renderChart()}
    </div>
  );
};

export default DataVisualization;
