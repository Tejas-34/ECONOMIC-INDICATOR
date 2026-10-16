import React from 'react';
import { useTickerStream } from '../../hooks/useTickerStream';
import styles from './Ticker.module.css';

export const Ticker: React.FC = () => {
  const { quotes, marketStatus, lastUpdated } = useTickerStream();

  // Create two identical contiguous halves for truly seamless infinite marquee loop
  const displayQuotes = React.useMemo(() => {
    if (quotes.length === 0) return [];
    // Ensure base sequence exceeds the 1214px viewport before duplicating
    const repeatCount = Math.max(2, Math.ceil(8 / quotes.length));
    const base: typeof quotes = [];
    for (let i = 0; i < repeatCount; i++) {
      base.push(...quotes);
    }
    // Exactly two identical halves: translating -50% shifts by exactly one half seamlessly
    return [...base, ...base];
  }, [quotes]);

  return (
    <nav className={styles.tickerContainer} aria-label="Live Market Quotes Ticker">
      <div className={styles.liveBadgeArea}>
        <div
          className={`${styles.liveBadge} ${
            marketStatus === 'CLOSED'
              ? styles.closedBadge
              : marketStatus === 'STALE'
              ? styles.staleBadge
              : ''
          }`}
          title={lastUpdated ? `Last updated: ${lastUpdated}` : undefined}
          data-testid="ticker-status-badge"
        >
          <span className={styles.liveText}>{marketStatus}</span>
          {marketStatus === 'LIVE' && (
            <span
              className={styles.liveDot}
              aria-hidden="true"
              data-testid="ticker-live-dot"
            />
          )}
        </div>
        <div className={styles.divider} aria-hidden="true" />
      </div>

      <div className={styles.marqueeViewport}>
        <div className={styles.marqueeTrack}>
          {displayQuotes.map((quote, idx) => {
            const formattedPrice = quote.currentPrice.toLocaleString('en-IN', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            });
            const formattedChange = `${quote.changePercent >= 0 ? '+' : ''}${quote.changePercent.toFixed(2)}%`;

            return (
              <React.Fragment key={`${quote.symbol}-${idx}`}>
                <div className={styles.quoteItem}>
                  <span className={styles.symbol}>{quote.symbol}</span>
                  <span
                    className={`${styles.priceChange} ${
                      quote.isPositive ? styles.positive : styles.negative
                    }`}
                  >
                    {formattedPrice} ({formattedChange})
                  </span>
                </div>
                <div className={styles.divider} aria-hidden="true" />
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </nav>
  );
};
