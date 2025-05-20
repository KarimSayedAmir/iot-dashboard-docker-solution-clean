import React, { useState } from 'react';
import { SelectedVariables } from '../types';

interface VariableSelectorProps {
  availableVariables: string[];
  selectedVariables: SelectedVariables;
  onSelectionChange: (selected: SelectedVariables) => void;
}

const VariableSelector: React.FC<VariableSelectorProps> = ({
  availableVariables,
  selectedVariables,
  onSelectionChange,
}) => {
  const handleCheckboxChange = (variable: string) => {
    const updated = {
      ...selectedVariables,
      [variable]: !selectedVariables[variable],
    };
    onSelectionChange(updated);
  };

  return (
    <div className="variable-selector">
      <h2>Variablenauswahl</h2>
      <div className="variable-list">
        {availableVariables.map((variable) => (
          <div key={variable} className="variable-item">
            <label>
              <input
                type="checkbox"
                checked={!!selectedVariables[variable]}
                onChange={() => handleCheckboxChange(variable)}
              />
              {variable}
            </label>
          </div>
        ))}
      </div>
    </div>
  );
};

export default VariableSelector;
