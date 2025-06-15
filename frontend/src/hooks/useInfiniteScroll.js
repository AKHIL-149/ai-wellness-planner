// frontend/src/hooks/useInfiniteScroll.js

import { useState, useEffect, useCallback } from 'react';

export const useInfiniteScroll = (fetchMore, hasMore = true, threshold = 1.0) => {
  const [isFetching, setIsFetching] = useState(false);

  const handleScroll = useCallback(() => {
    if (!hasMore || isFetching) return;

    const scrollTop = document.documentElement.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight;
    const clientHeight = document.documentElement.clientHeight;

    if (scrollTop + clientHeight >= scrollHeight * threshold) {
      setIsFetching(true);
    }
  }, [hasMore, isFetching, threshold]);

  useEffect(() => {
    if (!isFetching) return;
    
    const fetchData = async () => {
      try {
        await fetchMore();
      } finally {
        setIsFetching(false);
      }
    };

    fetchData();
  }, [isFetching, fetchMore]);

  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  return [isFetching, setIsFetching];
};