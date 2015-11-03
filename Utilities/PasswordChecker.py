# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a checker for password strength.
"""

from __future__ import unicode_literals

import re


class PasswordChecker(object):
    """
    Class implementing a checker for password strength.
    """
    Complexity_VeryWeak = 0
    Complexity_Weak = 1
    Complexity_Good = 2
    Complexity_Strong = 3
    Complexity_VeryStrong = 4
    
    Status_Failed = 0
    Status_Passed = 1
    Status_Exceeded = 2
    
    def __init__(self):
        """
        Constructor
        """
        self.score = {
            "count": 0,
            "adjusted": 0,
            "beforeRedundancy": 0
        }
        
        # complexity index
        self.complexity = {
            "limits": [20, 50, 60, 80, 100],
            "value": self.Complexity_VeryWeak
        }
        
        # check categories follow
        
        # length of the password
        self.passwordLength = {
            "count": 0,
            "minimum": 6,
            "status": self.Status_Failed,
            "rating": 0,
            "factor": 0.5,      # per character bonus
            "bonus": 10,        # minimum reached? Get a bonus.
            "penalty": -20,     # if we stay under minimum, we get punished
        }
        
        # recommended password length
        self.recommendedPasswordLength = {
            "count": 0,
            "minimum": 8,
            "status": self.Status_Failed,
            "rating": 0,
            "factor": 1.2,
            "bonus": 10,
            "penalty": -10,
        }
        
        # Basic requirements are:
        # 1) Password Length
        # 2) Uppercase letter use
        # 3) Lowercase letter use
        # 4) Numeric character use
        # 5) Symbol use
        self.basicRequirements = {
            "count": 0,
            "minimum": 3,       # have to be matched to get the bonus
            "status": self.Status_Failed,
            "rating": 0,
            "factor": 1.0,
            "bonus": 10,
            "penalty": -10,
        }
        
        # how much redundancy is permitted, if the password is
        # long enough. we will skip the redudancy penalty if this
        # number is not exceeded (meaning redundancy < this number)
        self.redundancy = {
            "value": 1,         # 1 means, not double characters,
                                # default to start
            "permitted": 2.0,   # 2 means, in average every character
                                # can occur twice
            "status": self.Status_Failed,
            "rating": 0,
        }
        
        # number of uppercase letters, such as A-Z
        self.uppercaseLetters = {
            "count": 0,
            "minimum": 1,
            "status": self.Status_Failed,
            "rating": 0,
            "factor": 0.0,
            "bonus": 10,
            "penalty": -10,
        }
        
        # number of lowercase letters, such as a-z
        self.lowercaseLetters = {
            "count": 0,
            "minimum": 1,
            "status": self.Status_Failed,
            "rating": 0,
            "factor": 0.0,
            "bonus": 10,
            "penalty": -10,
        }
        
        # number of numeric characters
        self.numerics = {
            "count": 0,
            "minimum": 1,
            "status": self.Status_Failed,
            "rating": 0,
            "factor": 0.0,
            "bonus": 10,
            "penalty": -10,
        }
        
        # number of symbol characters
        self.symbols = {
            "count": 0,
            "minimum": 1,
            "status": self.Status_Failed,
            "rating": 0,
            "factor": 0.0,
            "bonus": 10,
            "penalty": -10,
        }
        
        # number of dedicated symbols in the middle
        self.middleSymbols = {
            "count": 0,
            "minimum": 1,
            "status": self.Status_Failed,
            "rating": 0,
            "factor": 0.0,
            "bonus": 10,
            "penalty": -10,
        }
        
        # number of dedicated numbers in the middle
        self.middleNumerics = {
            "count": 0,
            "minimum": 1,
            "status": self.Status_Failed,
            "rating": 0,
            "factor": 0.0,
            "bonus": 10,
            "penalty": -10,
        }
        
        # how many sequential characters should be checked
        # such as "abc" or "MNO" to be not part of the password
        self.sequentialLetters = {
            "data": "abcdefghijklmnopqrstuvwxyz",
            "length": 3,
            
            "count": 0,
            "status": self.Status_Failed,
            "rating": 0,
            "factor": -1.0,
            "bonus": 0,
            "penalty": -10,
        }
        
        # how many sequential characters should be checked
        # such as "123" to be not part of the password
        self.sequentialNumerics = {
            "data": "0123456789",
            "length": 3,
            
            "count": 0,
            "status": self.Status_Failed,
            "rating": 0,
            "factor": -1.0,
            "bonus": 0,
            "penalty": -10,
        }
        
        # keyboard patterns to check, typical sequences from your
        # keyboard
        self.keyboardPatterns = {
            # German and English keyboard text
            "data": [
                "qwertzuiop", "asdfghjkl", "yxcvbnm", "!\"§$%&/()=",    # de
                "1234567890",   # de numbers
                "qaywsxedcrfvtgbzhnujmik,ol.pö-üä+#",   # de up-down
                
                "qwertyuiop", "asdfghjkl", "zyxcvbnm", "!@#$%^&*()_",   # en
                "1234567890",   # en numbers
                "qazwsxedcrfvtgbyhnujmik,ol.p;/[']\\",  # en up-down
            ],
            "length": 4,    # how long is the pattern to check and blame for?
            
            "count": 0,     # how many of these pattern can be found
            "status": self.Status_Failed,
            "rating": 0,
            "factor": -1.0,     # each occurrence is punished with that factor
            "bonus": 0,
            "penalty": -10,
        }
        
        # check for repeated sequences, like in catcat
        self.repeatedSequences = {
            "length": 3,
            
            "count": 0,
            "status": self.Status_Failed,
            "rating": 0,
            "factor": 0.0,
            "bonus": 0,
            "penalty": -10,
        }
        
        # check for repeated mirrored sequences, like in tactac
        self.mirroredSequences = {
            "length": 3,
            
            "count": 0,
            "status": self.Status_Failed,
            "rating": 0,
            "factor": 0.0,
            "bonus": 0,
            "penalty": -10,
        }
        
        self.uppercaseRe = re.compile("[A-Z]")
        self.lowercaseRe = re.compile("[a-z]")
        self.numberRe = re.compile("[0-9]")
        self.symbolRe = re.compile("[^a-zA-Z0-9]")
    
    def __strReverse(self, string):
        """
        Private method to reverse a string.
        
        @param string string to be reversed (string)
        @return reversed string (string)
        """
        return "".join(reversed(string))
    
    def __determineStatus(self, value):
        """
        Private method to determine the status.
        
        @param value value to check (integer)
        @return status (Status_Failed, Status_Passed, Status_Exceeded)
        """
        if value == 0:
            return self.Status_Passed
        elif value > 0:
            return self.Status_Exceeded
        else:
            return self.Status_Failed
    
    def __determineBinaryStatus(self, value):
        """
        Private method to determine a binary status.
        
        @param value value to check (integer)
        @return status (Status_Failed, Status_Passed)
        """
        if value == 0:
            return self.Status_Passed
        else:
            return self.Status_Failed
    
    def checkPassword(self, password):
        """
        Public method to check a given password.
        
        @param password password to be checked (string)
        @return indication for the password strength (Complexity_VeryWeak,
            Complexity_Weak, Complexity_Good, Complexity_Strong,
            Complexity_VeryStrong)
        """
        # how long is the password?
        self.passwordLength["count"] = len(password)
        self.recommendedPasswordLength["count"] = len(password)
        
        # Loop through password to check for Symbol, Numeric, Lowercase
        # and Uppercase pattern matches
        for index in range(len(password)):
            if self.uppercaseRe.match(password[index]):
                self.uppercaseLetters["count"] += 1
            elif self.lowercaseRe.match(password[index]):
                self.lowercaseLetters["count"] += 1
            elif self.numberRe.match(password[index]):
                if index > 0 and index < len(password) - 1:
                    self.middleNumerics["count"] += 1
                self.numerics["count"] += 1
            elif self.symbolRe.match(password[index]):
                if index > 0 and index < len(password) - 1:
                    self.middleSymbols["count"] += 1
                self.symbols["count"] += 1
        
        # check the variance of symbols or better the redundancy
        # makes only sense for at least two characters
        if len(password) > 1:
            uniqueCharacters = []
            for index1 in range(len(password)):
                found = False
                for index2 in range(index1 + 1, len(password)):
                    if password[index1] == password[index2]:
                        found = True
                        break
                if not found:
                    uniqueCharacters.append(password[index1])
            
            # calculate a redundancy number
            self.redundancy["value"] = len(password) / len(uniqueCharacters)
        
        # Check for sequential alpha string patterns (forward and reverse)
        # but only, if the string has already a length to check for, does
        # not make sense to check the password "ab" for the sequential data
        # "abc"
        lowercasedPassword = password.lower()
        
        if self.passwordLength["count"] >= self.sequentialLetters["length"]:
            for index in range(len(self.sequentialLetters["data"]) -
                               self.sequentialLetters["length"] + 1):
                fwd = self.sequentialLetters["data"][
                    index:index + self.sequentialLetters["length"]]
                rev = self.__strReverse(fwd)
                if lowercasedPassword.find(fwd) != -1:
                    self.sequentialLetters["count"] += 1
                if lowercasedPassword.find(rev) != -1:
                    self.sequentialLetters["count"] += 1
        
        # Check for sequential numeric string patterns (forward and reverse)
        if self.passwordLength["count"] >= self.sequentialNumerics["length"]:
            for index in range(len(self.sequentialNumerics["data"]) -
                               self.sequentialNumerics["length"] + 1):
                fwd = self.sequentialNumerics["data"][
                    index:index + self.sequentialNumerics["length"]]
                rev = self.__strReverse(fwd)
                if lowercasedPassword.find(fwd) != -1:
                    self.sequentialNumerics["count"] += 1
                if lowercasedPassword.find(rev) != -1:
                    self.sequentialNumerics["count"] += 1
        
        # Check common keyboard patterns
        patternsMatched = []
        if self.passwordLength["count"] >= self.keyboardPatterns["length"]:
            for pattern in self.keyboardPatterns["data"]:
                for index in range(
                        len(pattern) - self.keyboardPatterns["length"] + 1):
                    fwd = pattern[index:index +
                                  self.keyboardPatterns["length"]]
                    rev = self.__strReverse(fwd)
                    if lowercasedPassword.find(fwd) != -1:
                        if fwd not in patternsMatched:
                            self.keyboardPatterns["count"] += 1
                            patternsMatched.append(fwd)
                    if lowercasedPassword.find(rev) != -1:
                        if fwd not in patternsMatched:
                            self.keyboardPatterns["count"] += 1
                            patternsMatched.append(rev)
        
        # Try to find repeated sequences of characters.
        if self.passwordLength["count"] >= self.repeatedSequences["length"]:
            for index in range(len(lowercasedPassword) -
                               self.repeatedSequences["length"] + 1):
                fwd = lowercasedPassword[
                    index:index + self.repeatedSequences["length"]]
                if lowercasedPassword.find(
                   fwd, index + self.repeatedSequences["length"]) != -1:
                    self.repeatedSequences["count"] += 1
        
        # Try to find mirrored sequences of characters.
        if self.passwordLength["count"] >= self.mirroredSequences["length"]:
            for index in range(len(lowercasedPassword) -
                               self.mirroredSequences["length"] + 1):
                fwd = lowercasedPassword[
                    index:index + self.mirroredSequences["length"]]
                rev = self.__strReverse(fwd)
                if lowercasedPassword.find(
                   fwd, index + self.mirroredSequences["length"]) != -1:
                    self.mirroredSequences["count"] += 1
        
        # Initial score based on length
        self.score["count"] = self.passwordLength["count"] * \
            self.passwordLength["factor"]
        
        # passwordLength
        # credit additional length or punish "under" length
        if self.passwordLength["count"] >= self.passwordLength["minimum"]:
            # credit additional characters over minimum
            self.passwordLength["rating"] = self.passwordLength["bonus"] + \
                (self.passwordLength["count"] -
                 self.passwordLength["minimum"]) * \
                self.passwordLength["factor"]
        else:
            self.passwordLength["rating"] = self.passwordLength["penalty"]
        self.score["count"] += self.passwordLength["rating"]
        
        # recommendedPasswordLength
        # Credit reaching the recommended password length or put a
        # penalty on it
        if self.passwordLength["count"] >= \
                self.recommendedPasswordLength["minimum"]:
            self.recommendedPasswordLength["rating"] = \
                self.recommendedPasswordLength["bonus"] + \
                (self.passwordLength["count"] -
                 self.recommendedPasswordLength["minimum"]) * \
                self.recommendedPasswordLength["factor"]
        else:
            self.recommendedPasswordLength["rating"] = \
                self.recommendedPasswordLength["penalty"]
        self.score["count"] += self.recommendedPasswordLength["rating"]
        
        # lowercaseLetters
        # Honor or punish the lowercase letter use
        if self.lowercaseLetters["count"] > 0:
            self.lowercaseLetters["rating"] = \
                self.lowercaseLetters["bonus"] + \
                self.lowercaseLetters["count"] * \
                self.lowercaseLetters["factor"]
        else:
            self.lowercaseLetters["rating"] = self.lowercaseLetters["penalty"]
        self.score["count"] += self.lowercaseLetters["rating"]
        
        # uppercaseLetters
        # Honor or punish the lowercase letter use
        if self.uppercaseLetters["count"] > 0:
            self.uppercaseLetters["rating"] = \
                self.uppercaseLetters["bonus"] + \
                self.uppercaseLetters["count"] * \
                self.uppercaseLetters["factor"]
        else:
            self.uppercaseLetters["rating"] = self.uppercaseLetters["penalty"]
        self.score["count"] += self.uppercaseLetters["rating"]
        
        # numerics
        # Honor or punish the numerics use
        if self.numerics["count"] > 0:
            self.numerics["rating"] = self.numerics["bonus"] + \
                self.numerics["count"] * self.numerics["factor"]
        else:
            self.numerics["rating"] = self.numerics["penalty"]
        self.score["count"] += self.numerics["rating"]
        
        # symbols
        # Honor or punish the symbols use
        if self.symbols["count"] > 0:
            self.symbols["rating"] = self.symbols["bonus"] + \
                self.symbols["count"] * self.symbols["factor"]
        else:
            self.symbols["rating"] = self.symbols["penalty"]
        self.score["count"] += self.symbols["rating"]
        
        # middleSymbols
        # Honor or punish the middle symbols use
        if self.middleSymbols["count"] > 0:
            self.middleSymbols["rating"] = self.middleSymbols["bonus"] + \
                self.middleSymbols["count"] * self.middleSymbols["factor"]
        else:
            self.middleSymbols["rating"] = self.middleSymbols["penalty"]
        self.score["count"] += self.middleSymbols["rating"]
        
        # middleNumerics
        # Honor or punish the middle numerics use
        if self.middleNumerics["count"] > 0:
            self.middleNumerics["rating"] = self.middleNumerics["bonus"] + \
                self.middleNumerics["count"] * self.middleNumerics["factor"]
        else:
            self.middleNumerics["rating"] = self.middleNumerics["penalty"]
        self.score["count"] += self.middleNumerics["rating"]
        
        # sequentialLetters
        # Honor or punish the sequential letter use
        if self.sequentialLetters["count"] == 0:
            self.sequentialLetters["rating"] = \
                self.sequentialLetters["bonus"] + \
                self.sequentialLetters["count"] * \
                self.sequentialLetters["factor"]
        else:
            self.sequentialLetters["rating"] = \
                self.sequentialLetters["penalty"]
        self.score["count"] += self.sequentialLetters["rating"]
        
        # sequentialNumerics
        # Honor or punish the sequential numerics use
        if self.sequentialNumerics["count"] == 0:
            self.sequentialNumerics["rating"] = \
                self.sequentialNumerics["bonus"] + \
                self.sequentialNumerics["count"] * \
                self.sequentialNumerics["factor"]
        else:
            self.sequentialNumerics["rating"] = \
                self.sequentialNumerics["penalty"]
        self.score["count"] += self.sequentialNumerics["rating"]
        
        # keyboardPatterns
        # Honor or punish the keyboard patterns use
        if self.keyboardPatterns["count"] == 0:
            self.keyboardPatterns["rating"] = \
                self.keyboardPatterns["bonus"] + \
                self.keyboardPatterns["count"] * \
                self.keyboardPatterns["factor"]
        else:
            self.keyboardPatterns["rating"] = self.keyboardPatterns["penalty"]
        self.score["count"] += self.keyboardPatterns["rating"]
        
        # Count our basicRequirements and set the status
        self.basicRequirements["count"] = 0
        
        # password length
        self.passwordLength["status"] = self.__determineStatus(
            self.passwordLength["count"] - self.passwordLength["minimum"])
        if self.passwordLength["status"] != self.Status_Failed:
            # requirement met
            self.basicRequirements["count"] += 1
        
        # uppercase letters
        self.uppercaseLetters["status"] = self.__determineStatus(
            self.uppercaseLetters["count"] - self.uppercaseLetters["minimum"])
        if self.uppercaseLetters["status"] != self.Status_Failed:
            # requirement met
            self.basicRequirements["count"] += 1
        
        # lowercase letters
        self.lowercaseLetters["status"] = self.__determineStatus(
            self.lowercaseLetters["count"] - self.lowercaseLetters["minimum"])
        if self.lowercaseLetters["status"] != self.Status_Failed:
            # requirement met
            self.basicRequirements["count"] += 1
        
        # numerics
        self.numerics["status"] = self.__determineStatus(
            self.numerics["count"] - self.numerics["minimum"])
        if self.numerics["status"] != self.Status_Failed:
            # requirement met
            self.basicRequirements["count"] += 1
        
        # symbols
        self.symbols["status"] = self.__determineStatus(
            self.symbols["count"] - self.symbols["minimum"])
        if self.symbols["status"] != self.Status_Failed:
            # requirement met
            self.basicRequirements["count"] += 1
        
        # judge the requirement status
        self.basicRequirements["status"] = self.__determineStatus(
            self.basicRequirements["count"] -
            self.basicRequirements["minimum"])
        if self.basicRequirements["status"] != self.Status_Failed:
            self.basicRequirements["rating"] = \
                self.basicRequirements["bonus"] + \
                self.basicRequirements["factor"] * \
                self.basicRequirements["count"]
        else:
            self.basicRequirements["rating"] = \
                self.basicRequirements["penalty"]
        self.score["count"] += self.basicRequirements["rating"]
        
        # beyond basic requirements
        self.recommendedPasswordLength["status"] = self.__determineStatus(
            self.recommendedPasswordLength["count"] -
            self.recommendedPasswordLength["minimum"])
        self.middleNumerics["status"] = self.__determineStatus(
            self.middleNumerics["count"] -
            self.middleNumerics["minimum"])
        self.middleSymbols["status"] = self.__determineStatus(
            self.middleSymbols["count"] -
            self.middleSymbols["minimum"])
        self.sequentialLetters["status"] = self.__determineBinaryStatus(
            self.sequentialLetters["count"])
        self.sequentialNumerics["status"] = self.__determineBinaryStatus(
            self.sequentialNumerics["count"])
        self.keyboardPatterns["status"] = self.__determineBinaryStatus(
            self.keyboardPatterns["count"])
        self.repeatedSequences["status"] = self.__determineBinaryStatus(
            self.repeatedSequences["count"])
        self.mirroredSequences["status"] = self.__determineBinaryStatus(
            self.mirroredSequences["count"])
        
        # we apply them only, if the length is not awesome
        if self.recommendedPasswordLength["status"] != self.Status_Exceeded:
            # repeatedSequences
            # Honor or punish the use of repeated sequences
            if self.repeatedSequences["count"] == 0:
                self.repeatedSequences["rating"] = \
                    self.repeatedSequences["bonus"]
            else:
                self.repeatedSequences["rating"] = \
                    self.repeatedSequences["penalty"] + \
                    self.repeatedSequences["count"] * \
                    self.repeatedSequences["factor"]
            
            # mirroredSequences
            # Honor or punish the use of mirrored sequences
            if self.mirroredSequences["count"] == 0:
                self.mirroredSequences["rating"] = \
                    self.mirroredSequences["bonus"]
            else:
                self.mirroredSequences["rating"] = \
                    self.mirroredSequences["penalty"] + \
                    self.mirroredSequences["count"] * \
                    self.mirroredSequences["factor"]
        
        # save value before redundancy
        self.score["beforeRedundancy"] = self.score["count"]
        
        # apply the redundancy
        # is the password length requirement fulfilled?
        if self.recommendedPasswordLength["status"] != self.Status_Exceeded:
            # full penalty, because password is not long enough, only for
            # a positive score
            if self.score["count"] > 0:
                self.score["count"] *= 1.0 / self.redundancy["value"]
        
        # level it out
        if self.score["count"] > 100:
            self.score["adjusted"] = 100
        elif self.score["count"] < 0:
            self.score["adjusted"] = 0
        else:
            self.score["adjusted"] = self.score["count"]
        
        # judge it
        for index in range(len(self.complexity["limits"])):
            if self.score["adjusted"] <= self.complexity["limits"][index]:
                self.complexity["value"] = index
                break
        
        return self.complexity["value"]

if __name__ == "__main__":
    while True:
        try:
            pwd = input("Enter password: ")
            print(pwd, PasswordChecker().checkPassword(pwd))
        except KeyboardInterrupt:
            break
