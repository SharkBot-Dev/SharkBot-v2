"use client";
import { useState, useEffect } from "react";
import ToggleButton from "./ToggleButton";

interface ModuleToggleProps {
  guild_id: string;
  module_name: string;
  label?: string;
}

export default function ModuleToggle({
  guild_id,
  module_name,
  label = "モジュール有効化",
}: ModuleToggleProps) {
  const [isEnabled, setEnabled] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    const fetchData = async () => {
      try {
        const response = await fetch(`/api/module/${guild_id}/is_enable/${module_name}`);
        const json = await response.json();
        if (isMounted) {
          setEnabled(json.enabled);
          setIsLoading(false);
        }
      } catch (error) {
        console.error("Failed to fetch module status:", error);
        if (isMounted) setIsLoading(false);
      }
    };

    fetchData();
    return () => { isMounted = false; };
  }, [guild_id, module_name]);

  const handleChange = async (checked: boolean) => {
    const previousState = isEnabled;
    setEnabled(checked);

    try {
      const response = await fetch(`/api/module/${guild_id}/toggle/${module_name}`, {
        method: 'POST',
      });
      const json = await response.json();
      setEnabled(json.enabled);
    } catch (error) {
      console.error("Failed to toggle module:", error);
      setEnabled(previousState); 
    }
  };

  return (
    <div className="flex items-center gap-3">
      {label && (
        <span className="text-sm font-medium text-white-700">
          {label}
        </span>
      )}
      
      {isLoading && <span className="text-xs text-white-400">Loading...</span>}

      <ToggleButton 
        name="module_enabled" 
        value={isEnabled} 
        onChange={handleChange} 
      />
    </div>
  );
}