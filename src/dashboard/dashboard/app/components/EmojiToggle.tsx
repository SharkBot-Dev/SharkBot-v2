"use client";

import { useEffect, useState } from "react";
import ToggleButton from "./ToggleButton";

export function EmojiToggle({
  emojiId,
  defaultOn,
}: {
  emojiId: string;
  defaultOn: boolean;
}) {
  const [enabled, setEnabled] = useState(defaultOn);

  useEffect(() => {
    setEnabled(defaultOn);
  }, [defaultOn]);

  return (
    <>
      <ToggleButton
        name={`toggle_${emojiId}`}
        defaultValue={defaultOn}
        onChange={setEnabled}
      />

      {enabled && (
        <input
          type="hidden"
          name="emoji"
          value={emojiId}
        />
      )}
    </>
  );
}