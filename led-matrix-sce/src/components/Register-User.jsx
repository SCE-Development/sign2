import React, { useState } from 'react';
import '../styles/Register-User.css';

const MAIN_URL = import.meta.env.VITE_MAIN_URL;
const API_KEY = import.meta.env.VITE_API_KEY;

function RegisterUser({ userData, setUserData }) {
  const [LeetCodeUsername, setLeetcodeUsername] = useState('');
  const [message, setMessage] = useState(''); // State to hold the success or error message
  const [isSuccess, setIsSuccess] = useState(false);
  const [confirmUsername, setConfirmUsername] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [isMatching, setIsMatching] = useState(true);
  const [isDisabled, setIsDisabled] = useState(false);


  const handleRegisterUser = async (e) => {
    e.preventDefault();
    if (LeetCodeUsername !== confirmUsername) {
      setMessage('Usernames do not match. Please try again.');
      setIsMatching(false);
      return; // Prevent form submission
    }
    const userData = {
      username: LeetCodeUsername,
      first_name: firstName,
      last_name: lastName
    }

    setMessage('');
    setIsMatching(true);
    setIsDisabled(true);

    try {
      const response = await fetch(`${MAIN_URL}/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": `${API_KEY}`, // Add the API key in the header
        },
        body: JSON.stringify(userData),
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Registration successful:", data);
        setMessage(`User ${data.userInfo.username} registered successfully!`);
        setIsSuccess(true); // Indicate success

        // Clear the form fields after successful registration
        setLeetcodeUsername('');
        setConfirmUsername('');
        setFirstName('');
        setLastName('');
      } else {
        const errorData = await response.json();
        if (errorData.detail === "User already exists") {
          setMessage(`<span style={{ color: 'red' }}>Error: ${errorData.detail}</span>`);
          setLeetcodeUsername('');
          setConfirmUsername('');
          setFirstName('');
          setLastName('');
        } else {
          console.error("Registration failed:", errorData.detail || response.statusText);
          setMessage(`Error: ${errorData.detail || response.statusText}`);
        }
        setIsSuccess(false); // Indicate error
      }
    } catch (error) {
      console.error("Error during fetch:", error);
    }
    setUserData(userData);
    setTimeout(() => {
      setIsDisabled(false);
    }, 5000);
  };

  return (
    <div className='register-container'>
      <form onSubmit={handleRegisterUser} id="form">
        <div className='register-form'>
          <h1>Register User</h1>
          <br />
          <input
            type="text"
            placeholder="First Name"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            id="first-name-input"
          />
          <br />
          <input
            type="text"
            placeholder="Last Name"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            id="last-name-input"
          />
          <br />
          <input
            type="text"
            placeholder="Enter LeetCode Username"
            value={LeetCodeUsername}
            onChange={(e) => setLeetcodeUsername(e.target.value)}
            id="username-input"
          />
          <br />
          <input
            type="text"
            placeholder="Confirm LeetCode Username"
            value={confirmUsername}
            onChange={(e) => setConfirmUsername(e.target.value)}
            id="confirm-username-input"
          />
          <button id="register-button" type="submit" disabled={isDisabled}>{isDisabled ? "Please wait..." : "Register User"}</button>
          <p className={`message ${isMatching ? "success-message" : "error-message"}`}>{message}</p>
        </div>
      </form>
    </div>
  );
}

export default RegisterUser;
