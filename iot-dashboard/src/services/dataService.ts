import axios from 'axios';
import { IoTData, ManualData } from '../types';

// Use environment variable with fallback
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api';

console.log('API_BASE_URL:', API_BASE_URL);

// Interface for stored week data
export interface StoredWeekData {
  id: string;
  start_date: string;
  end_date: string;
  data_type: 'telemetry' | 'totalAmount' | 'both';
  iotData: IoTData[];
  manualCorrections: ManualData[];
  created_at: number;
  last_modified: number;
}

// Generate a unique ID for a week based on start and end dates
const generateWeekId = (startDate: string, endDate: string): string => {
  return `week_${startDate.replace(/\//g, '-')}_to_${endDate.replace(/\//g, '-')}`;
};

// Save week data to backend
export const saveWeekData = async (
  startDate: string,
  endDate: string,
  dataType: 'telemetry' | 'totalAmount' | 'both',
  iotData: IoTData[],
  manualCorrections: ManualData[] = []
): Promise<string> => {
  try {
    const response = await axios.post(`${API_BASE_URL}/weeks`, {
      startDate,
      endDate,
      dataType,
      iotData,
      manualCorrections
    });
    
    if (!response.data || !response.data.id) {
      throw new Error('Invalid response from server');
    }
    
    return response.data.id;
  } catch (error) {
    console.error('Error saving week data:', error);
    throw new Error('Failed to save week data. Please try again.');
  }
};

// Get all stored weeks
export const getAllWeeks = async (): Promise<StoredWeekData[]> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/weeks`);
    
    if (!Array.isArray(response.data)) {
      console.error('Invalid response format:', response.data);
      return [];
    }
    
    // Validiere die Daten
    const validWeeks = response.data.filter((week: any) => {
      return (
        week &&
        typeof week.id === 'string' &&
        typeof week.start_date === 'string' &&
        typeof week.end_date === 'string' &&
        ['telemetry', 'totalAmount', 'both'].includes(week.data_type)
      );
    });
    
    return validWeeks;
  } catch (error) {
    console.error('Error getting all weeks:', error);
    return [];
  }
};

// Get week data by ID
export const getWeekData = async (weekId: string): Promise<StoredWeekData | null> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/weeks/${weekId}`);
    
    if (!response.data || !response.data.id) {
      return null;
    }
    
    return response.data;
  } catch (error) {
    console.error('Error getting week data:', error);
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null;
    }
    throw new Error('Failed to load week data. Please try again.');
  }
};

// Update manual corrections for a specific week
export const updateManualCorrections = async (
  weekId: string,
  manualCorrections: ManualData[]
): Promise<void> => {
  try {
    // Delete existing corrections
    const week = await getWeekData(weekId);
    if (week && week.manualCorrections) {
      for (const correction of week.manualCorrections) {
        await axios.delete(`${API_BASE_URL}/weeks/${weekId}/corrections/${correction.id}`);
      }
    }
    
    // Add new corrections
    for (const correction of manualCorrections) {
      await axios.post(`${API_BASE_URL}/weeks/${weekId}/corrections`, correction);
    }
  } catch (error) {
    console.error('Error updating manual corrections:', error);
    throw new Error('Failed to update corrections. Please try again.');
  }
};

// Delete week data
export const deleteWeekData = async (weekId: string): Promise<void> => {
  try {
    await axios.delete(`${API_BASE_URL}/weeks/${weekId}`);
  } catch (error) {
    console.error('Error deleting week data:', error);
    throw new Error('Failed to delete week data. Please try again.');
  }
};
