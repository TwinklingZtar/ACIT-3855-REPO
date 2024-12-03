
const express = require('express');
const axios = require('axios');
const path = require('path');
const cors = require('cors');

const PORT = 3000;

const app = express();
app.use(cors());

app.use(express.static(path.join(__dirname, 'public')));


let currentData = {
    dataFromEndpoint1: null,
    dataFromEndpoint2: { error: 'No data available' },
    dataFromEndpoint3: { error: 'No data available' }
};

// Function to fetch data from all endpoints
async function fetchData() {
    try {
        const response1 = await axios.get('http://kafka-acit3855.eastus.cloudapp.azure.com:8100/stats/eventlog');
        currentData.dataFromEndpoint1 = response1.data;
    } catch (error) {
        console.error('Error fetching data from endpoint1:', error.message);
        currentData.dataFromEndpoint1 = { error: 'Failed to fetch data from endpoint1' };
    }

    try {
        const randomIndex = Math.floor(Math.random() * 101);
        const response2 = await axios.get(`http://kafka-acit3855.eastus.cloudapp.azure.com:8110/party-list/create-open-party?index=${randomIndex}`);
        currentData.dataFromEndpoint2 = response2.data;
        currentData.dataFromEndpoint2["rIndex"] = randomIndex
    } catch (error) {
        console.error('Error fetching data from endpoint2:', error.message);
        currentData.dataFromEndpoint2 = { error: 'Failed to fetch data from endpoint2' };
    }

    try {
        const randomIndex = Math.floor(Math.random() * 101);
        const response3 = await axios.get(`http://kafka-acit3855.eastus.cloudapp.azure.com:8110/party-list/join-open-party?index=${randomIndex}`);
        currentData.dataFromEndpoint3 = response3.data;
        currentData.dataFromEndpoint3["rIndex"] = randomIndex
    } catch (error) {
        console.error('Error fetching data from endpoint3:', error.message);
        currentData.dataFromEndpoint3 = { error: 'Failed to fetch data from endpoint3' };
    }

    try {
        const response4 = await axios.get(`http://kafka-acit3855.eastus.cloudapp.azure.com:8120/anomalies?anomaly_type=createOpen`);
        currentData.dataFromEndpoint4 = response4.data[0];
    } catch (error) {
        console.error('Error fetching data from endpoint4:', error.message);
        currentData.dataFromEndpoint4 = { error: 'Failed to fetch data from endpoint4' };
    }

    try {
        const response5 = await axios.get(`http://kafka-acit3855.eastus.cloudapp.azure.com:8120/anomalies?anomaly_type=joinOpen`);
        currentData.dataFromEndpoint5 = response5.data[0];
    } catch (error) {
        console.error('Error fetching data from endpoint5:', error.message);
        currentData.dataFromEndpoint5 = { error: 'Failed to fetch data from endpoint5' };
    }
}

// Fetch data every 5 seconds
setInterval(fetchData, 5000);

// Route to get the latest data
app.get('/api/data', (req, res) => {
    res.json(currentData);
});



// Start server and listen on all IPs (0.0.0.0) and the specified port
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server is running on http://localhost:${PORT}`);
    fetchData(); // Initial fetch to have data ready immediately
});

//'0.0.0.0',