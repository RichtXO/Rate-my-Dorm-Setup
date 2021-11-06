import "@/typedef";

import axios from "axios";

const client = axios.create({
    baseURL: "/api",
});


export const getPost = () =>
    client.get("")