import axios from "axios";

const client = axios.create({
    baseURL: "/api",
});

export const login = (userInfo) => client.post("/session", userInfo);

export const signup = (userInfo) => client.post("/users", userInfo);

export const getUserInfo = (username) => client.get(`/users/${username}`);

export const follow = (user, followingUser) => client.post("/follow", user, followingUser);

export const getFollowers = (user) => client.post(`/followers/${user}`);

export const getFollowing = (user) => client.get(`/following/${user}`);
