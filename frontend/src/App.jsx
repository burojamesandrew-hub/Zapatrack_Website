import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import TrackRequest from './pages/TrackRequest';
import NotFound from './pages/NotFound';
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ display:'flex', flexDirection:'column', minHeight:'100svh' }}>
        <Navbar />
        <Routes>
          <Route path="/"           element={<Home />} />
          <Route path="/track"      element={<TrackRequest />} />
          <Route path="/track/:id"  element={<TrackRequest />} />
          <Route path="*"           element={<NotFound />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
