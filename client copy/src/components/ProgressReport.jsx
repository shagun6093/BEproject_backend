import React from "react";
import { Line, Pie, Bar } from "react-chartjs-2";
import {
  Chart,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

// Register Chart.js modules
Chart.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

// Sample JSON data for tasks
const sampleTasks = [
  {
    taskId: 1,
    taskName: "Reframe Negative Thoughts",
    userResponse: "I feel no one loves me.",
    taskFeedback: "Your response shows initial awareness.",
    performanceScore: "Good",
    creationDate: "2023-08-01T10:00:00Z",
    completionDate: "2023-08-01T10:20:00Z",
  },
  {
    taskId: 2,
    taskName: "Mindfulness Exercise",
    userResponse: "I was anxious but calmer after the exercise.",
    taskFeedback: "Very Good – you’re starting to connect with your breathing.",
    performanceScore: "Very Good",
    creationDate: "2023-08-03T11:00:00Z",
    completionDate: "2023-08-03T11:15:00Z",
  },
  {
    taskId: 3,
    taskName: "CBT Journaling",
    userResponse: "I felt overwhelmed with negative self-talk.",
    taskFeedback: "Good, but keep practicing reframing.",
    performanceScore: "Good",
    creationDate: "2023-08-05T09:00:00Z",
    completionDate: "2023-08-05T09:45:00Z",
  },
  {
    taskId: 4,
    taskName: "Reframing",
    userResponse: "I still struggle with criticism, but I’m aware.",
    taskFeedback: "Poor; try additional self-compassion exercises.",
    performanceScore: "Poor",
    creationDate: "2023-08-07T14:00:00Z",
    completionDate: "2023-08-07T14:50:00Z",
  },
  {
    taskId: 5,
    taskName: "CBT Journaling",
    userResponse: "After reframing my thoughts, I felt more optimistic.",
    taskFeedback: "Excellent job; your progress is clear.",
    performanceScore: "Excellent",
    creationDate: "2023-08-10T08:30:00Z",
    completionDate: "2023-08-10T08:50:00Z",
  },
];

// Utility to convert performance labels to a numeric value
const performanceMapping = {
  Excellent: 4,
  "Very Good": 3,
  Good: 2,
  Poor: 1,
};

// Calculate task completion duration in minutes
const getDurationMinutes = (creationDate, completionDate) => {
  const start = new Date(creationDate);
  const end = new Date(completionDate);
  return Math.round((end - start) / (1000 * 60));
};

// Sort tasks by taskId (or creation date)
const tasksSorted = sampleTasks.sort((a, b) => a.taskId - b.taskId);

// Prepare data for the Line Chart (Growth Over Time)
const lineData = {
  labels: tasksSorted.map((task) => `Task ${task.taskId}`),
  datasets: [
    {
      label: "Performance Score",
      data: tasksSorted.map((task) => performanceMapping[task.performanceScore]),
      fill: false,
      backgroundColor: "rgba(75,192,192,0.6)",
      borderColor: "rgba(75,192,192,1)",
      tension: 0.2,
    },
  ],
};

// Prepare data for the Pie Chart (Performance Distribution)
const performanceCounts = { Excellent: 0, "Very Good": 0, Good: 0, Poor: 0 };
tasksSorted.forEach((task) => {
  if (performanceCounts.hasOwnProperty(task.performanceScore)) {
    performanceCounts[task.performanceScore] += 1;
  }
});
const pieData = {
  labels: Object.keys(performanceCounts),
  datasets: [
    {
      label: "Task Performance",
      data: Object.values(performanceCounts),
      backgroundColor: [
        "rgba(75,192,192,0.6)",
        "rgba(54,162,235,0.6)",
        "rgba(255,206,86,0.6)",
        "rgba(255,99,132,0.6)",
      ],
      borderColor: [
        "rgba(75,192,192,1)",
        "rgba(54,162,235,1)",
        "rgba(255,206,86,1)",
        "rgba(255,99,132,1)",
      ],
      borderWidth: 1,
    },
  ],
};

// Prepare data for the Bar Chart (Task Completion Speed)
const barData = {
  labels: tasksSorted.map((task) => `Task ${task.taskId}`),
  datasets: [
    {
      label: "Completion Time (minutes)",
      data: tasksSorted.map((task) =>
        getDurationMinutes(task.creationDate, task.completionDate)
      ),
      backgroundColor: "rgba(153,102,255,0.6)",
      borderColor: "rgba(153,102,255,1)",
      borderWidth: 1,
    },
  ],
};

const commonOptions = {
  responsive: true,
  animation: {
    duration: 1000,
    easing: "easeOutQuart",
  },
  plugins: {
    legend: {
      position: "top",
    },
  },
};

const lineOptions = {
  ...commonOptions,
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        stepSize: 1,
      },
      title: {
        display: true,
        text: "Performance Score (1 = Poor, 4 = Excellent)",
      },
    },
    x: {
      title: {
        display: true,
        text: "Task Sequence",
      },
    },
  },
};

const pieOptions = {
  ...commonOptions,
  plugins: {
    ...commonOptions.plugins,
    title: {
      display: true,
      text: "Task Performance Distribution",
    },
  },
};

const barOptions = {
  ...commonOptions,
  scales: {
    y: {
      beginAtZero: true,
      title: {
        display: true,
        text: "Completion Time (minutes)",
      },
    },
    x: {
      title: {
        display: true,
        text: "Task ID",
      },
    },
  },
};

// CSS for a compact, centered dashboard container with animations
const dashboardStyle = {
  fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
  background: "linear-gradient(135deg, #f5f7fa, #c3cfe2)",
  padding: "20px",
  borderRadius: "12px",
  boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
  animation: "fadeIn 1s ease-out",
  margin: "0 auto",
  maxWidth: "800px",
};

const chartContainerStyle = {
  marginBottom: "30px",
  height: "200px", // Reduced height for each chart container
};

export default function ProgressDashboard() {
  return (
    <div style={{ textAlign: "center", padding: "20px" }}>
      <h1 style={{ marginBottom: "20px", color: "#333" }}>Progress Dashboard</h1>
      <div style={dashboardStyle}>
        {/* Line Chart */}
        <div style={chartContainerStyle}>
          <h2 style={{ marginBottom: "10px" }}>Growth Over Time</h2>
          <Line data={lineData} options={lineOptions} />
        </div>
        {/* Pie Chart */}
        <div style={chartContainerStyle}>
          <h2 style={{ marginBottom: "10px" }}>Performance Distribution</h2>
          <Pie data={pieData} options={pieOptions} />
        </div>
        {/* Bar Chart */}
        <div style={chartContainerStyle}>
          <h2 style={{ marginBottom: "10px" }}>Task Completion Speed</h2>
          <Bar data={barData} options={barOptions} />
        </div>
      </div>

      {/* CSS keyframes for animation */}
      <style>
        {`
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `}
      </style>
    </div>
  );
}
