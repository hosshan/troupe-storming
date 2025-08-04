import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import WorldsPage from "./pages/WorldsPage";
import CharactersPage from "./pages/CharactersPage";
import DiscussionsPage from "./pages/DiscussionsPage";
import DiscussionResultsPage from "./pages/DiscussionResultsPage";


function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background">
        <header className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container mx-auto px-4 h-16 flex items-center">
            <h1 className="text-xl font-semibold tracking-tight">
              TinyTroupe Brainstorming
            </h1>
          </div>
        </header>
        <main className="pb-8">
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
        </main>
      </div>
    </Router>
  );
}

export default App;
