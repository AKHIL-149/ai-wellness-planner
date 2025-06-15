// frontend/src/hooks/useMediaQuery.js

import { useState, useEffect } from 'react';

export const useMediaQuery = (query) => {
  const [matches, setMatches] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false;
  });

  useEffect(() => {
    const media = window.matchMedia(query);
    
    const updateMatch = () => {
      setMatches(media.matches);
    };

    updateMatch();
    media.addListener(updateMatch);

    return () => {
      media.removeListener(updateMatch);
    };
  }, [query]);

  return matches;
};