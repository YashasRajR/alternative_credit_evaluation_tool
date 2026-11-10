import React from "react";
import ReactDOM from "react-dom/client";
import "@fontsource-variable/anek-latin/standard.css";
import "@fontsource-variable/anek-devanagari/standard.css";
import "@fontsource/hind/400.css";
import "@fontsource/hind/500.css";
import "@fontsource/hind/600.css";
import App from "./App.jsx";
import "./styles/base.css";
import "./styles/paper.css";
import "./styles/result.css";
import "./styles/stamp.css";
import "./styles/tape.css";
import "./styles/dashboard.css";
import "./styles/form.css";
import "./styles/responsive.css";
import "./styles/print.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
