import FileUpload from "../components/FileUpload";
import Button from "../components/Buttons";
import '../styles/Announcement-Dashboard.css';
import PresetVideo from "../components/PresetVideo";
import PresetImage from "../components/PresetImage";
const AnnouncementDashboard = () => {
    return (
        <div className="announcement-container">
            <div className="image-upload-section">
                <FileUpload />
            </div>
            <div className="button-section">
                <Button />
            </div>
            <div className="preset-video-section">
                <PresetVideo />
            </div>
            <div className="preset-image-section">
                <PresetImage />
            </div>
        </div>
    )
}

export default AnnouncementDashboard;