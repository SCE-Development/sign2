import React, { useState } from 'react';
import '../styles/FileUpload.css';
const MAIN_URL = import.meta.env.VITE_MAIN_URL;
const API_KEY = import.meta.env.VITE_API_KEY;


const FileUpload = () => {
    const [selectedImage, setSelectedImage] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState("");

    const handleImageChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setSelectedImage(file);
            // Create preview URL
            const objectUrl = URL.createObjectURL(file);
            setPreviewUrl(objectUrl);

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


    const handleImageUpload = async () => {
        if (!selectedImage || isUploading) return;

        setIsUploading(true);
        const formData = new FormData();
        formData.append('file', selectedImage);

        try {
            // First call to kill the current process
            await fetch(`${MAIN_URL}/uploadImage`, {
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
        } catch (error) {
            console.error('Error:', error);
        } finally {
            setIsUploading(false);
        }
    };

    const resetImage = () => {
        setSelectedImage(null);
        setError("");
        // Clean up the preview URL
        if (previewUrl) {
            URL.revokeObjectURL(previewUrl);
            setPreviewUrl(null);
        }
    }

    return (
        <>
            <div className="file-upload-container">
                <div className="image-upload-section">
                    <div className="announcement-text">
                        <h1 className="">Announcements</h1>
                        <h3>Upload your announcement here, and it will be displayed on the LED Matrix!</h3>
                        <p><strong><em>Ensure your image or video is square</em></strong></p>
                    </div>
                    <div className="upload-box">
                        <input
                            type="file"
                            accept="image/*,video/*"
                            onChange={handleImageChange}
                            id="image-input"
                            className="file-input"
                        />
                        <label htmlFor="image-input" className="upload-label">
                            {!selectedImage ? 'Choose an image or video' : ''}
                        </label>
                        {previewUrl && (
                            <div className="preview-container">
                                <img
                                    src={previewUrl}
                                    alt="Preview"
                                    className="image-preview"
                                />
                            </div>
                        )}
                    </div>
                    {error && (
                        <p className="error-message">
                            Please input a square image.
                        </p>
                    )}
                    <div className="button-container">
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
            </div>
        </>
    );
};

export default FileUpload;