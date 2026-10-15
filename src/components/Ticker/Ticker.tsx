import React from 'react';
import { useTickerStream } from '../../hooks/useTickerStream';
import styles from './Ticker.module.css';

export const Ticker: React.FC = () => {
  const { quotes } = useTickerStream();

  // Create duplicate set for seamless continuous marquee loop
  const displayQuotes = quotes.length > 0 ? [...quotes, ...quotes, ...quotes] : [];

  return (
    <nav className={styles.tickerContainer} aria-label="Live Market Quotes Ticker">
      <div className={styles.liveBadgeArea}>
        <div className={styles.liveBadge}>
          <span>LIVE</span>
          <span className={styles.liveDot} aria-hidden="true" />
        </div>
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
              <div key={`${quote.symbol}-${idx}`} className={styles.quoteItem}>
                <span className={styles.symbol}>{quote.symbol}</span>
                <span
                  className={`${styles.priceChange} ${
                    quote.isPositive ? styles.positive : styles.negative
                  }`}
                >
                  {formattedPrice} ({formattedChange})
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </nav>
  );
};
