import React from 'react';
import '../styles/LEDsign.css';

const LEDsign = () => {
  return (
    <div className='main-container'>
      <div className="led-preview">
        <iframe
          id="led-frame"
          src="http://192.168.69.123:8888"  // URL of the emulator
          title="LED Emulator"
          scrolling="no"
        />
      </div>
    </div>
  );
};

export default LEDsign;
