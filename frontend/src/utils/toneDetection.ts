/**
 * Tone Detection Utility
 * 
 * Detects tone mismatch between custom greeting and personality.
 * Only warns for Professional personality with casual indicators.
 * 
 * This helps maintain consistency between the greeting tone and
 * the bot's response templates.
 */

const CASUAL_WORDS = [
  'hey', 'hiya', "what's up", 'sup', 'yay', 'woohoo', 'oops',
  'awesome', 'cool', 'totally', 'super', 'kinda', 'gonna', 'wanna',
  'lol', 'haha', 'omg'
];

const EMOJI_PATTERN = /[👋😊🔥✨🎉💖🤔😍😕🙏😎👍🙌💫🥳😤😅]/;
const EXCLAMATION_PATTERN = /!{2,}/;
const CAPS_PATTERN = /[A-Z]{3,}/;

/**
 * Check if there's a tone mismatch between the greeting and personality.
 * Only returns true for Professional personality with casual indicators.
 * 
 * @param customGreeting - The custom greeting text to check
 * @param personality - The selected personality type
 * @returns true if there's a mismatch, false otherwise
 */
export function hasToneMismatch(customGreeting: string, personality: string): boolean {
  if (personality !== 'professional' || !customGreeting) {
    return false;
  }
  
  if (EMOJI_PATTERN.test(customGreeting)) {
    return true;
  }
  
  if (EXCLAMATION_PATTERN.test(customGreeting)) {
    return true;
  }
  
  const lowerGreeting = customGreeting.toLowerCase();
  if (CASUAL_WORDS.some(word => lowerGreeting.includes(word))) {
    return true;
  }
  
  if (CAPS_PATTERN.test(customGreeting)) {
    return true;
  }
  
  return false;
}

/**
 * Get the specific reasons for tone mismatch.
 * Returns an array of detected casual indicators.
 * 
 * @param greeting - The greeting text to analyze
 * @returns Array of reason strings
 */
export function getToneMismatchReasons(greeting: string): string[] {
  const reasons: string[] = [];
  
  if (EMOJI_PATTERN.test(greeting)) {
    reasons.push('emojis');
  }
  if (EXCLAMATION_PATTERN.test(greeting)) {
    reasons.push('multiple exclamation marks');
  }
  
  const lowerGreeting = greeting.toLowerCase();
  const foundCasualWords = CASUAL_WORDS.filter(word => lowerGreeting.includes(word));
  if (foundCasualWords.length > 0) {
    reasons.push('casual language');
  }
  
  if (CAPS_PATTERN.test(greeting)) {
    reasons.push('enthusiastic capitalization');
  }
  
  return reasons;
}

/**
 * Generate a human-readable warning message for tone mismatch.
 * 
 * @param greeting - The greeting text to analyze
 * @returns Warning message string, or empty string if no mismatch
 */
export function getToneMismatchMessage(greeting: string): string {
  const reasons = getToneMismatchReasons(greeting);
  
  if (reasons.length === 0) {
    return '';
  }
  
  return `Your greeting has a friendly tone (${reasons.join(', ')}) but you selected Professional personality. This may confuse customers when responses don't match the greeting tone.`;
}

/**
 * Check if the greeting tone already matches the personality.
 * Returns true when no transformation is needed.
 * 
 * @param customGreeting - The custom greeting text to check
 * @param personality - The selected personality type
 * @returns true if tone matches, false if transformation might help
 */
export function isToneMatch(customGreeting: string, personality: string): boolean {
  if (!customGreeting || customGreeting.trim().length === 0) {
    return false;
  }
  
  if (personality === 'professional') {
    return !hasToneMismatch(customGreeting, personality);
  }
  
  if (personality === 'enthusiastic') {
    const hasEnthusiasm = 
      EMOJI_PATTERN.test(customGreeting) ||
      EXCLAMATION_PATTERN.test(customGreeting) ||
      CAPS_PATTERN.test(customGreeting);
    return hasEnthusiasm;
  }
  
  return true;
}
