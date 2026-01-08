"""
Password generation utilities.

Provides secure password generation using a pattern-only approach:
- Pattern-based generation (specify character types at each position)
"""

import secrets
import string


class PasswordGenerator:
    """Generates secure passwords using position-based patterns only."""

    # Define character sets as class constants for reusability
    LOWERCASE = string.ascii_lowercase
    UPPERCASE = string.ascii_uppercase
    DIGITS = string.digits
    SPECIAL = "!@#$%^&*"

    def generate(self, pattern: str) -> str:
        """
        Generate a secure random password from a position-based pattern string.

        Args:
            pattern: String where each character specifies the type for that position:
                - 'U' = uppercase letter (A-Z)
                - 'L' = lowercase letter (a-z)
                - 'N' = digit (0-9)
                - 'S' = symbol (!@#$%^&*)

        Returns:
            Generated password string

        Raises:
            ValueError: If pattern is empty or contains invalid characters

        Examples:
            # Pattern-based: first 5 uppercase, rest numbers
            pwd = PasswordGenerator().generate(pattern="UUUUUNNNNNN")

            # Pattern-based: symbols at first and last, numbers in middle
            pwd = PasswordGenerator().generate(pattern="SNNNNNNNNS")
        """
        return self._generate_from_pattern(pattern)

    def _generate_from_pattern(self, pattern: str) -> str:
        """
        Generate password from a position-based pattern string.

        Args:
            pattern: String where each character specifies the type for that position:
                - 'U' = uppercase letter (A-Z)
                - 'L' = lowercase letter (a-z)
                - 'N' = digit (0-9)
                - 'S' = symbol (!@#$%^&*)

        Returns:
            Generated password string

        Raises:
            ValueError: If pattern is empty or contains invalid characters

        Time Complexity: O(n) where n is pattern length
        Space Complexity: O(n) for the output password
        """
        if not pattern:
            raise ValueError("Pattern cannot be empty")

        # Validate pattern contains only valid characters
        valid_chars = set("ULNS")
        invalid_chars = set(pattern.upper()) - valid_chars
        if invalid_chars:
            raise ValueError(
                f"Pattern contains invalid characters: {', '.join(sorted(invalid_chars))}. "
                f"Valid characters are: U (uppercase), L (lowercase), N (numbers), S (symbols)"
            )

        # Mapping of pattern characters to character sets
        char_map = {
            "U": self.UPPERCASE,
            "L": self.LOWERCASE,
            "N": self.DIGITS,
            "S": self.SPECIAL,
        }

        # Generate password character by character based on pattern
        password_chars = []
        for char_type in pattern.upper():
            password_chars.append(secrets.choice(char_map[char_type]))

        return "".join(password_chars)
