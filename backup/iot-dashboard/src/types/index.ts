export interface IoTData {
  Time: string;
  PH_58: number;
  TEMP_WASSER_58: number;
  Water_Level: number;
  Trübung_Zulauf: number;
  Trubidity_Auslass: number;
  Flow_Rate_1: number;
  Flow_Rate_2: number;
  ARA_Flow: number;
  PH_59: number;
  TEMP_WASSER_59: number;
  [key: string]: string | number; // Für dynamische Zugriffe
}

export interface ManualData {
  weekStartDate: string;
  weekEndDate: string;
  pumpDuration: number; // Stunden
  totalFlowARA: number; // m³
  totalFlowGalgenkanal: number; // m³
  notes: string;
  [key: string]: string | number; // Für dynamische Zugriffe
}

export interface SelectedVariables {
  [key: string]: boolean;
}

export interface ChartConfig {
  type: 'line' | 'bar';
  variables: string[];
  title: string;
  yAxisLabel: string;
  timeRange: 'day' | 'week' | 'custom';
  customStartDate?: string;
  customEndDate?: string;
}
