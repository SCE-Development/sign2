import React from 'react';
import { useState, useEffect } from 'react';
import "../styles/Admin.css"

const MAIN_URL = import.meta.env.VITE_MAIN_URL;

const AdminList = ({ userData }) => {
    const [testData, setTestData] = useState([]);
    const [isEditing, setIsEditing] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch(`${MAIN_URL}/leaderboard`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }

                const result = await response.json();
                setTestData(result.users || result);  // Fallback in case result is an array
            } catch (error) {
                console.error("Error fetching leaderboard:", error);
            }
        };

        fetchData();
    }, [userData]);

    const deleteUser = async (username) => {
        const response = await fetch(`${MAIN_URL}/deleteUser`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username: username })
        });
        if (response.ok) {
            setTestData(prevData => prevData.filter(user => user.username !== username));
        }
    };

    /*
    #This is still in progress

    const UpdateUser = async (oldUser, newUser) => {
        const response = await fetch(`${url}updateUsername`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'api-key': `${key}`
            },
            body: JSON.stringify({ oldUser: oldUser, newUser: newUser })
        });
        if (response.ok) {
            fetchData();
        }
    };
    */

    return (
        <div className="admin-panel">
            <div className="admin-panel-header">
                <h1 className="admin-panel-title">Admin List</h1>
                <button
                    className="admin-panel-button"
                    onClick={() => setIsEditing(!isEditing)}
                >
                    {isEditing ? "Done" : "Edit"}
                </button>
            </div>
            <div className="admin-panel-list" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                <ul>
                    {testData.map((item) => (
                        <li key={item.username} className="admin-panel-item">
                            {isEditing ? (
                                <>
                                    <input
                                        type="text"
                                        className="admin-panel-input"
                                        defaultValue={item.username}
                                        placeholder={item.username}
                                    />
                                </>
                            ) : (
                                <>
                                    <div>
                                        {item.first_name} {item.last_name}
                                        <div className="admin-username">{item.username}</div>
                                    </div>
                                </>
                            )}
                            {isEditing && (
                                <div className="admin-panel-actions">
                                    <button
                                        className="admin-panel-update-button"
                                        onClick={() => {
                                            const newUsername = document.querySelector(
                                                `input[placeholder="${item.username}"]`
                                            ).value;
                                            updateUser(item.username, newUsername);
                                        }}
                                    >
                                        Update
                                    </button>
                                    <button
                                        className="admin-panel-delete-button"
                                        onClick={() => deleteUser(item.username)}
                                    >
                                        Delete
                                    </button>
                                </div>
                            )}
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    )
}

export default AdminList