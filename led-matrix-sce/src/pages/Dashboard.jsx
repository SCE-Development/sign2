import React, { useState } from 'react';
import LEDsign from '../components/LEDsign';
import RegisterUser from '../components/Register-User';
import '../styles/Dashboard.css'
import AdminList from '../components/AdminList';
import Buttons from '../components/Buttons';
export const Dashboard = () => {
  const [userData, setUserData] = useState([]);
  const urlParams = new URLSearchParams(window.location.search);
  const isAdmin = urlParams.get('isAdmin') === 'true';

  return (
    <div className='containter'>
      <div className='grid-container'>
        <div className="led-sign">
          <LEDsign />
        </div>
        <div className="button-container">
          <Buttons />
        </div>
        <div className={isAdmin ? "register-panel" : "register-panel-centered"}>
          <RegisterUser userData={userData} setUserData={setUserData} />
        </div>
        {isAdmin && (
          <div className="admin-panel">
            <AdminList userData={userData} />
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard;