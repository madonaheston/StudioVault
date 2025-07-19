import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Dashboard = () => {
    const [name, setName] = useState('');
    const [galleries, setGalleries] = useState([]);
    const [selectedGallery, setSelectedGallery] = useState('');
    const [file, setFile] = useState(null);
    const [error, setError] = useState('');

    const fetchGalleries = async () => {
        try {
            const token = localStorage.getItem('token');
            const res = await axios.get('http://localhost:5000/api/galleries', {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            setGalleries(res.data.galleries);
        } catch (err) {
            setError('Error fetching galleries');
        }
    };

    useEffect(() => {
        fetchGalleries();
    }, []);

    const togglePublic = async (id, isPublic) => {
        try {
            const token = localStorage.getItem('token');
            await axios.put(`http://localhost:5000/api/galleries/${id}`, { is_public: !isPublic }, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            fetchGalleries();
        } catch (err) {
            setError('Error updating gallery');
        }
    };

    const handleGallerySubmit = async (e) => {
        e.preventDefault();
        try {
            const token = localStorage.getItem('token');
            await axios.post('http://localhost:5000/api/galleries', { name }, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            setName('');
            // Refresh galleries
            const res = await axios.get('http://localhost:5000/api/galleries', {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            setGalleries(res.data.galleries);
        } catch (err) {
            setError('Error creating gallery');
        }
    };

    const handleImageSubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', file);
        try {
            const token = localStorage.getItem('token');
            await axios.post(`http://localhost:5000/api/galleries/${selectedGallery}/upload`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    Authorization: `Bearer ${token}`
                }
            });
            setFile(null);
            setSelectedGallery('');
        } catch (err) {
            setError('Error uploading image');
        }
    };

    return (
        <div>
            <h2>Photographer Dashboard</h2>
            <h3>Create New Gallery</h3>
            {error && <p>{error}</p>}
            <form onSubmit={handleGallerySubmit}>
                <div>
                    <label>Gallery Name</label>
                    <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
                </div>
                <button type="submit">Create Gallery</button>
            </form>
            <h3>Upload Image</h3>
            <form onSubmit={handleImageSubmit}>
                <div>
                    <label>Select Gallery</label>
                    <select value={selectedGallery} onChange={(e) => setSelectedGallery(e.target.value)}>
                        <option>Select a gallery</option>
                        {galleries.map(gallery => (
                            <option key={gallery.id} value={gallery.id}>{gallery.name}</option>
                        ))}
                    </select>
                </div>
                <div>
                    <label>Image</label>
                    <input type="file" onChange={(e) => setFile(e.target.files[0])} />
                </div>
                <button type="submit">Upload</button>
            </form>
            <hr />
            <h2>My Galleries</h2>
            {galleries.map(gallery => (
                <div key={gallery.id}>
                    <h3><a href={`/galleries/${gallery.id}`}>{gallery.name}</a></h3>
                    <label>
                        <input
                            type="checkbox"
                            checked={gallery.is_public}
                            onChange={() => togglePublic(gallery.id, gallery.is_public)}
                        />
                        Public
                    </label>
                </div>
            ))}
        </div>
    );
};

export default Dashboard;
