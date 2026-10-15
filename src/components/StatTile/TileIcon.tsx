import React from 'react';

interface TileIconProps {
  iconKey?: string;
  className?: string;
}

const ICON_MAP: Record<string, string> = {
  india: '/image-9450.png',
  us: '/image-9440.png',
  world: '/image-9510.png',
  exports: '/exports-3d.png',
  imports: '/imports-3d.png',
  gst: '/image-9600.png',
  coins: '/image-9580.png',
  inflation: '/image-9590.png',
  target: '/rbi-target-3d.png',
  expenditure: '/total-expenditure-3d.png',
  parliament: '/capital-expenditure-3d.png',
};

export const TileIcon: React.FC<TileIconProps> = ({ iconKey, className }) => {
  if (!iconKey) return null;

  const src = ICON_MAP[iconKey];
  if (!src) return null;

  return (
    <img
      src={src}
      alt={iconKey}
      className={className}
      loading="eager"
      decoding="async"
    />
  );
};

