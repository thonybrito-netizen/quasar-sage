// Spec Section 6: a four-pointed geometric pulsar star, points disconnected
// at the center (negative-space cross). Top=cyan, right=amber, bottom=neon
// green, left=crimson -- exactly Section 6.2's color assignment.
export function PulsarMark({ size = 40 }: { size?: number }) {
  const gap = 6; // the deliberate negative-space cross, per Section 6.3
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* top point (cyan) */}
      <path d={`M50,${2} L${50 + 14},${50 - gap} L50,${50 - gap - 6} L${50 - 14},${50 - gap} Z`} fill="#22D3EE" />
      {/* right point (amber) */}
      <path d={`M${98},50 L${50 + gap},${50 + 14} L${50 + gap + 6},50 L${50 + gap},${50 - 14} Z`} fill="#F59E0B" />
      {/* bottom point (neon green) */}
      <path d={`M50,${98} L${50 - 14},${50 + gap} L50,${50 + gap + 6} L${50 + 14},${50 + gap} Z`} fill="#22C55E" />
      {/* left point (crimson) */}
      <path d={`M${2},50 L${50 - gap},${50 - 14} L${50 - gap - 6},50 L${50 - gap},${50 + 14} Z`} fill="#EF4444" />
    </svg>
  );
}
