/**
 * Formats a numeric value into a human-readable string with appropriate suffix.
 * 
 * @param num - The numeric value to format.
 * @returns A formatted string with the appropriate suffix, or 'N/A' if the input is invalid.
 */
export const formatNumeric = (num: number): string => {
  if (num === null || num === undefined || isNaN(num)) return 'N/A';

  if (num >= 1e12) {
    return `${(num / 1e12).toFixed(2)}T`;
  } else if (num >= 1e9) {
    return `${(num / 1e9).toFixed(2)}B`;
  } else if (num >= 1e6) {
    return `${(num / 1e6).toFixed(2)}M`;
  } else if (num >= 1e3) {
    return `${(num / 1e3).toFixed(2)}K`;
  }

  return num.toString();
};