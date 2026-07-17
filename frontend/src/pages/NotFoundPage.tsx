/** 404 Not Found Page */
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Brain, ArrowLeft } from 'lucide-react';

export function NotFoundPage() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center">
        <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-cyan-500/20 to-violet-600/20 flex items-center justify-center mb-6 border border-white/10">
          <Brain className="w-10 h-10 text-cyan-400" />
        </div>
        <h1 className="text-7xl font-bold gradient-text mb-4">404</h1>
        <h2 className="text-xl font-semibold mb-2">Page not found</h2>
        <p className="text-muted-foreground mb-6 max-w-sm">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 bg-gradient-to-r from-cyan-500 to-violet-600 text-white font-semibold px-6 py-2.5 rounded-xl shadow-lg hover:opacity-90 transition-opacity"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>
      </motion.div>
    </div>
  );
}
