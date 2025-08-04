import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Container from "@mui/material/Container";
import WorldsPage from "./pages/WorldsPage";
import CharactersPage from "./pages/CharactersPage";
import DiscussionsPage from "./pages/DiscussionsPage";
import DiscussionResultsPage from "./pages/DiscussionResultsPage";

const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#1976d2",
    },
    secondary: {
      main: "#dc004e",
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              TinyTroupe Brainstorming
            </Typography>
          </Toolbar>
        </AppBar>
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
          <Routes>
            <Route path="/" element={<WorldsPage />} />
            <Route path="/worlds" element={<WorldsPage />} />
            <Route path="/characters/:worldId" element={<CharactersPage />} />
            <Route path="/discussions/:worldId" element={<DiscussionsPage />} />
            <Route
              path="/discussions/:worldId/results/:discussionId"
              element={<DiscussionResultsPage />}
            />
          </Routes>
        </Container>
      </Router>
    </ThemeProvider>
  );
}

export default App;
