import React from 'react';
import '../styles/ReturnButton.css';
import { useNavigate } from 'react-router-dom';

const ReturnButton = () => {
  const navigate = useNavigate();

  return (
    <div className="return-button-container">
      <button
        className="return-button"
        onClick={() => navigate('/')}
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 24 24">
          <g fill="none" stroke="#000" stroke-linecap="round" stroke-linejoin="round" stroke-width="2">
            <path d="m8 5l-5 5l5 5" /><path d="M3 10h8c5.523 0 10 4.477 10 10v1" />
          </g>
        </svg>
      </button>
    </div>
  );
};

export default ReturnButton;