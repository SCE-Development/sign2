import React, { useState } from 'react';
import '../styles/AnnouncementDashboard.css';
import ReturnButton from '../components/ReturnButton';
const MAIN_URL = import.meta.env.VITE_MAIN_URL;
const API_KEY = import.meta.env.VITE_API_KEY;


const AnnouncementDashboard = () => {
    const [selectedImage, setSelectedImage] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState("");

    const handleImageChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setSelectedImage(file);
            // check if the image is a square
            const reader = new FileReader();

            reader.onload = () => {
                const img = new Image();
                img.src = reader.result;

                img.onload = () => {
                    if (img.width === img.height) {
                        setError("");
                    } else {
                        setError("Image is not square");
                    }
                }
            }
            reader.readAsDataURL(file);
        }
    };

    /*
    Okay so here i have this upload image function that uploads an image to the server, use 
    the end point i have set used here already. So just make sure your payload is correct.
    The actual end point is `${MAIN_URL}/uploadImage`
    You can find it the main.py file in the core_files folder.
    I dont want you to really test it since i know it does and it might break something, as
    long as you format the way i have it below, it should work.
    So you can put your code in this file, and i will test it out and see if it works.
    For now use the buttons component in your announcement dashboard.
    Also use components to make it easier to manage the code.
    So like the part that takes the image should be its own component.
    and the preset images little box should be its own component.
    and the video part should be its own component.
    Feel free to nuke the code i have here, i will not be offended.
    Just make sure it works.
    */
    const handleImageUpload = async () => {
        if (!selectedImage) return;

        setIsUploading(true);
        const formData = new FormData();
        formData.append('file', selectedImage);

        try {
            const response = await fetch(`${MAIN_URL}/uploadImage`, {
                method: 'POST',
                headers: {
                    'x-api-key': API_KEY,
                },
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            const data = await response.json();
            console.log('Success:', data);
            // Optionally add success message or notification here
        } catch (error) {
            console.error('Error:', error);
            // Optionally add error message or notification here
        } finally {
            setIsUploading(false);
        }
    };

    const resetImage = () => {
        setSelectedImage(null);
        setError("");
    }

    return (
        <>
            <ReturnButton/>
            <div className="announcement-container">
                <h1 className="">Announcements</h1>
                <h3>Upload your announcement here, and it will be displayed on the LED Matrix!</h3>
                <p><strong><em>Ensure your image or video is square</em></strong></p>
                <div className="image-upload-section">
                    <div className="upload-box">
                        <input
                            type="file"
                            accept="image/*,video/*"
                            onChange={handleImageChange}
                            id="image-input"
                            className="file-input"
                        />
                        <label htmlFor="image-input" className="upload-label">
                            {selectedImage ? selectedImage.name : 'Choose an image or video'}
                        </label>
                    </div>
                    {error && (
                        <p className="error-message">
                            Please input a square image.
                        </p>
                    )}
                    <button
                        className="submit-button"
                        disabled={!selectedImage || isUploading || error}
                        onClick={handleImageUpload}
                    >
                        {isUploading ? 'Uploading...' : 'Upload'}
                    </button>
                    {selectedImage && (
                        <button
                            className="reset-button"
                            onClick={resetImage}
                        >
                            Reset
                        </button>
                    )}
                </div>
            </div>
        </>
    );
};

export default AnnouncementDashboard;