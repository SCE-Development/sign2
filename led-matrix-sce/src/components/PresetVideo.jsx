import React from 'react';
import '../styles/PresetVideo.css';

const PresetVideo = () => {
  // Array of 9 preset videos (you can modify this later with actual presets)
  const presets = Array(9).fill(null);

  return (
    <div className="preset-video-container">
      <h1 className="preset-video-title">Preset Videos</h1>
      <div className="preset-video-grid">
        {presets.map((_, index) => (
          <div key={index} className="preset-video-item">
            {<button>Preset {index + 1}</button>}
          </div>
        ))}
      </div>
    </div>
  );
};

export default PresetVideo;
