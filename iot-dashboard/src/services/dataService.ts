import axios from 'axios';
import { IoTData, ManualData } from '../types';

// Base URL for the API
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3000/api';

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
    
    return response.data.id;
  } catch (error) {
    console.error('Error saving week data:', error);
    throw error;
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
    throw error;
  }
};

// Get week data by ID
export const getWeekData = async (weekId: string): Promise<StoredWeekData | null> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/weeks/${weekId}`);
    return response.data;
  } catch (error) {
    console.error('Error getting week data:', error);
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null;
    }
    throw error;
  }
};

// Get all stored weeks
export const getAllWeeks = async (): Promise<StoredWeekData[]> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/weeks`);
    return response.data;
  } catch (error) {
    console.error('Error getting all weeks:', error);
    return [];
  }
};

// Delete week data
export const deleteWeekData = async (weekId: string): Promise<void> => {
  try {
    await axios.delete(`${API_BASE_URL}/weeks/${weekId}`);
  } catch (error) {
    console.error('Error deleting week data:', error);
    throw error;
  }
};
