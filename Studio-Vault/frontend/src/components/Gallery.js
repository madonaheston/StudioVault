import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Gallery = ({ match }) => {
    const [images, setImages] = useState([]);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchImages = async () => {
            try {
                const res = await axios.get(`http://localhost:5000/api/galleries/${match.params.id}/images`);
                setImages(res.data.images);
            } catch (err) {
                setError('Error fetching images');
            }
        };
        fetchImages();
    }, [match.params.id]);

    return (
        <div>
            <h2>Gallery</h2>
            {error && <p>{error}</p>}
            <div>
                {images.map(image => (
                    <img key={image.id} src={`http://localhost:5000/uploads/${image.filename}`} alt="" />
                ))}
            </div>
        </div>
    );
};

export default Gallery;
