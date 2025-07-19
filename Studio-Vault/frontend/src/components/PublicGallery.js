import React, { useState, useEffect } from 'react';
import axios from 'axios';

const PublicGallery = ({ match }) => {
    const [gallery, setGallery] = useState(null);
    const [images, setImages] = useState([]);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchGallery = async () => {
            try {
                const res = await axios.get(`http://localhost:5000/api/public/galleries/${match.params.id}`);
                setGallery(res.data.gallery);
                setImages(res.data.images);
            } catch (err) {
                setError('Error fetching gallery');
            }
        };
        fetchGallery();
    }, [match.params.id]);

    if (error) {
        return <div>{error}</div>;
    }

    if (!gallery) {
        return <div>Loading...</div>;
    }

    const [comment, setComment] = useState('');
    const [comments, setComments] = useState({});
    const [likes, setLikes] = useState({});

    useEffect(() => {
        images.forEach(image => {
            fetchComments(image.id);
            fetchLikes(image.id);
        });
    }, [images]);

    const fetchComments = async (imageId) => {
        try {
            const res = await axios.get(`http://localhost:5000/api/images/${imageId}/comments`);
            setComments(prev => ({ ...prev, [imageId]: res.data.comments }));
        } catch (err) {
            setError('Error fetching comments');
        }
    };

    const fetchLikes = async (imageId) => {
        try {
            const res = await axios.get(`http://localhost:5000/api/images/${imageId}/likes`);
            setLikes(prev => ({ ...prev, [imageId]: res.data.likes }));
        } catch (err) {
            setError('Error fetching likes');
        }
    };

    const handleCommentSubmit = async (e, imageId) => {
        e.preventDefault();
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                setError('You must be logged in to comment');
                return;
            }
            await axios.post(`http://localhost:5000/api/images/${imageId}/comments`, { text: comment }, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            setComment('');
            fetchComments(imageId);
        } catch (err) {
            setError('Error adding comment');
        }
    };

    const handleLike = async (imageId) => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                setError('You must be logged in to like an image');
                return;
            }
            await axios.post(`http://localhost:5000/api/images/${imageId}/likes`, {}, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            fetchLikes(imageId);
        } catch (err) {
            setError('Error liking image');
        }
    };

    const [rating, setRating] = useState(0);

    const handleRatingSubmit = async (e) => {
        e.preventDefault();
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                setError('You must be logged in to rate a photographer');
                return;
            }
            await axios.post(`http://localhost:5000/api/photographers/${gallery.photographer_id}/ratings`, { value: rating }, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            setRating(0);
        } catch (err) {
            setError('Error adding rating');
        }
    };

    return (
        <div>
            <h2>{gallery.name}</h2>
            <h3>Rate this Photographer</h3>
            <form onSubmit={handleRatingSubmit}>
                <select value={rating} onChange={(e) => setRating(e.target.value)}>
                    <option value="0">Select a rating</option>
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                    <option value="4">4</option>
                    <option value="5">5</option>
                </select>
                <button type="submit">Rate</button>
            </form>
            <hr />
            <div>
                {images.map(image => (
                    <div key={image.id}>
                        <img src={`http://localhost:5000/uploads/${image.filename}`} alt="" />
                        <p>{likes[image.id] || 0} likes</p>
                        <button onClick={() => handleLike(image.id)}>Heart</button>
                        <div>
                            {comments[image.id] && comments[image.id].map(comment => (
                                <p key={comment.id}><strong>{comment.user}:</strong> {comment.text}</p>
                            ))}
                        </div>
                        <form onSubmit={(e) => handleCommentSubmit(e, image.id)}>
                            <input type="text" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Add a comment" />
                            <button type="submit">Comment</button>
                        </form>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default PublicGallery;
