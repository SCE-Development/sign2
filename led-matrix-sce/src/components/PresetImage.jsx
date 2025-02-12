import React from 'react';
import '../styles/PresetImage.css';

const PresetImage = () => {
    // Array of 9 preset images (you can modify this later with actual presets)
    const presets = Array(9).fill(null);

    return (
        <div className="preset-image-container">
            <h1 className="preset-image-title">Preset Images</h1>
            <div className="preset-image-grid">
                {presets.map((_, index) => (
                    <div key={index} className="preset-image-item">
                        {<button>Preset {index + 1}</button>}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default PresetImage;
