import queue
from queue import LifoQueue
import re

class Variable:

    def __init__(self, name, statementType, scope, value):
        self.name = name
        self.statementType = statementType
        self.scope = scope
        self.value = value
    
class Function:
    def __init__(self, name, statementType, scope, pharameters):
        self.name = name
        self.statementType = statementType
        self.scope = scope
        self.pharameters = pharameters


class SemanticReader:
    
    def __init__(self):     
        self.stopWords = ["if", "while", "void", "string", "int", "float", "=", "==", ">", "<", "return", "{", "}", "(", ")"]
        self.symbolTable = {}
        self.lastFunction = None
        self.brackets = {"{" : 0, "}" : 0, "(" : 0, ")" : 0}
        self.errors = 0

    def readCode(self, codeName): 
        lines = queue.Queue()
        self.openFileCode(lines, codeName)
        self.startReading(lines)       

    def openFileCode(self, lines, codeName):
        with open(codeName, "r") as code:                          
            for line in code:
                lines.put(line.strip('\n'))

    def startReading(self, lines):
        for numLine in range (lines.qsize()):
            currentLine = lines.get()
            if currentLine != "":
                self.readingLine(currentLine, numLine)
        print (str(self.errors) + " error(s) found")

    def readingLine(self, currentline, numLine):
        self.checkStatement(self.groupingWordfromLine(currentline), numLine)

    def groupingWordfromLine(self, currentline):
        groupWords = currentline.split(" ")
        groupWords.reverse()
        self.deleteSpaces(groupWords)
        return groupWords

    def deleteSpaces(self, groupWords):
        copyGroupWords = groupWords.copy()
        while True:
            if copyGroupWords.pop() == "":
                groupWords.pop()
            else:
                break

    def checkStatement(self, groupWords, numLine):
        first = groupWords.pop()
        first = self.checkFunctionNameCall(first, groupWords)
        if self.inStopWords(first):
            
            self.checkStopWord(first, groupWords, numLine)        

        elif self.inSymbolTable(first):
            
            if not self.checkVariableInSymbolTable(first, groupWords):
                if not self.checkFunctionInSymbolTable(first, groupWords):
                    print("Error at the line: " + str(numLine) + ". Invalid statement")     
                    self.errors += 1        

        else:
            print("Error at the line: " + str(numLine) + ". Unknown error")
            self.errors += 1

    def checkFunctionNameCall(self, first, groupWords):
        if first.find("(") != -1 :
            first = first.split("(")
            data = first.pop()
            groupWords.append(data)
            first = first.pop()
        return first

    def inStopWords(self, word):
        return word in self.stopWords

    def inSymbolTable(self, word):
        return word in self.symbolTable

    def checkStopWord(self, first, groupWords, numLine):
        if first == "return":
                if not self.checkReturn(first, groupWords):
                    print("Error at the line: " + str(numLine) + ". Invalid value return")
                    self.errors += 1
        elif first == "}":
            if not self.checkCloseBracket(first):
                print("Error at the line: " + str(numLine) + ". Check the bracket")
                self.errors += 1
        else:
            if self.checkIfCycleDeclaration(first):
                if not self.checkIfOrCycle(first, groupWords):
                    print("Error at the line: " + str(numLine) + ". Invalid Condition")
                    self.errors += 1
            elif self.checkDeclarationName(groupWords) != -1:
                if not self.checkFunction(first, groupWords, numLine):
                    print("Error at the line: " + str(numLine) + ". Invalid function")
                    self.errors += 1
            else:
                b, name1 = self.checkVariable(first, groupWords, numLine)
                if not b:
                    print("Error at the line: " + str(numLine + 1) + ". Invalid variable = " + str(name1))
                    self.errors += 1

    def checkReturn(self, first, groupWords):
        returnData = groupWords.pop()
        lastFunctionType = self.symbolTable [self.lastFunction]
        lastFunctionType = lastFunctionType.statementType
        if self.inSymbolTable(returnData):
            data = self.symbolTable [returnData]
            data = data.statementType
            if self.getLastFunction() != "global":                
                if data == lastFunctionType:
                    return True
        elif self.checkTypeOfData(returnData) == lastFunctionType:
            return True
        else:            
            return False
    
    def checkCloseBracket(self, first):
        self.brackets ["}"] = self.brackets.get("}") + 1
        if self.brackets.get("{") == self.brackets.get("}"):
            self.VerifyScope()
            self.lastFunction = None
            return True
        return False

    def VerifyScope(self):
        keys = list(self.symbolTable.keys())
        for key in keys:
            value = self.symbolTable.get(key)
            if value.scope == self.lastFunction:
                del self.symbolTable [key]

    def checkIfCycleDeclaration(self, first):
        return first == "if" or first == "while" or first == "for"

    def checkIfOrCycle(self, first, groupWords):        
        firstCondition = groupWords.pop()
        if firstCondition[:1].find("(") != -1:
            comparator = groupWords.pop()
            if comparator == "=" or comparator == "==" or comparator == "<" or comparator == ">":
                secondCondition = groupWords.pop()
                if secondCondition.find("){",0, len(secondCondition) - 1):
                    self.brackets ["{"] = self.brackets.get("{") + 1
                    return True 
        return False

    def checkDeclarationName(self, groupWords):
        copyGroupWords = groupWords.copy()
        name = copyGroupWords.pop()
        return name.find("(")
            
    def checkFunction(self, statementType, groupWords, numLine):
        pharametersOfFunction = {}
        name = groupWords.pop()
        name = name.split(sep='(')
        firstVariableType = name.pop()
        name = name.pop()
        firstVariableName = groupWords.pop()
        if firstVariableName.find(")") != -1:
            if self.checkLastPharameter(pharametersOfFunction, firstVariableType, firstVariableName):
                self.symbolTable [name] = Function(name, statementType, self.getLastFunction(), pharametersOfFunction)
                self.lastFunction = name
                return True
        elif firstVariableName.find(",") != -1:
            
            firstVariableName = firstVariableName [:len(firstVariableName ) - 1]
            
            pharametersOfFunction [firstVariableName] = firstVariableType
            if self.checkMorePharameter(pharametersOfFunction, groupWords):
                self.symbolTable [name] = Function(name, statementType, self.getLastFunction(), pharametersOfFunction)
                self.lastFunction = name
                return True
        else:
            return False

    def checkLastPharameter(self, pharametersOfFunction, firstVariableType, firstVariableName):
        firstVariableName = firstVariableName.split(sep=')')
        bracket = firstVariableName.pop()
        if bracket == "{":
            self.brackets [bracket] = self.brackets.get(bracket) + 1
            firstVariableName = firstVariableName.pop()
            pharametersOfFunction [firstVariableName] = firstVariableType
            return True
        else:
            return False

    def checkMorePharameter(self, pharametersOfFunction, groupWords):
        nextType = groupWords.pop()
        nextName = groupWords.pop()
        while nextName.find(",") != -1:

            nextName = nextName [:len(nextName ) - 1]
            pharametersOfFunction [nextName] = nextType
            nextType = groupWords.pop()
            nextName = groupWords.pop()
        return self.checkLastPharameter(pharametersOfFunction, nextType, nextName)

    def checkVariable(self, statementType, groupWords, numLine):
        name = groupWords.pop()
        # print(name)
        equals = groupWords.pop()
        if equals == "=":
            value = groupWords.pop()
            value = self.checkIfValueIsAFunction(value)
            if self.checkValueOfStatement(statementType, value):
                
                self.symbolTable [name] = Variable(name, statementType, self.getLastFunction(), value)
                return True, ""
            elif self.getLastFunction() != "global":
                
                pharameters = self.symbolTable.get(self.getLastFunction())
                pharameters = pharameters.pharameters
                if pharameters.get(value) == statementType:
                    self.symbolTable [name] = Variable(name, statementType, self.getLastFunction(), value)
                    return True, ""
            else:
                return False, name
        return False, name    

    def checkIfValueIsAFunction(self, value):
        
        if value.find("(") != -1 and value.find(")") != -1:
        
            value = value.split("(")
            functionValue = value.pop()
            functionValue = functionValue [:len(functionValue ) - 1]
            if self.symbolTable.get(functionValue) != None or self.checkTypeOfData(functionValue):
                valueName = value.pop()
                if self.symbolTable.get(valueName) != None:
                    functionValues = self.symbolTable.get(valueName)
                    value = functionValues.statementType
            else:
                return False

        return value


    def checkVariableInSymbolTable (self, first, groupWords):
        equal = groupWords.copy()
        equal = equal.pop()
        if equal == "=":
            groupWords.pop()
            value = groupWords.pop()
            
            variable =  self.symbolTable [first]
            variable.value = value
            self.symbolTable [first] = Variable(first, variable.statementType, variable.scope, value)
            return True
        return False

    def checkFunctionInSymbolTable(self, first, groupWords):
        pharameters = self.symbolTable.get(first)
        pharameters = pharameters.pharameters
        pharameters = list(pharameters.values())
        if len(pharameters) == 0 and len(groupWords) == 0:
            return True
        if len(pharameters) == len(groupWords):
            i = 0
            while len(groupWords) != 0:
                data = groupWords.pop()
                
                data = data [:len(data ) - 1]
                data = self.checkTypeOfData(data)
                if pharameters.index(data) == i:
                    i =+ 1
                else:
                    return False
            return True
        return False
        
    def checkValueOfStatement(self, statementType, value):
        return self.getTypeOfValueinString(value) == statementType

    def getLastFunction(self):
        if self.lastFunction is None:
            return "global"
        return self.lastFunction

    def getTypeOfValueinString(self, value):
        if self.symbolTable.get(value) != None:
            statement = self.symbolTable [value]
            return statement.statementType
            
        else:
            
            if self.isInt(value) or value == "int":
                return "int"
            elif self.isFloat(value) or value == "float":
                return "float"
            elif str(value):
                return "string"
            else:                   
                return False

    def checkTypeOfData(self, value):
        if self.isInt(value) or value == "int":
            return "int"
        elif self.isFloat(value) or value == "float":
            return "float"
        else:
            value2 = value[0]
            value2 += value[len(value) - 1]
            if value2 == '""':
                    return "string"
            else:                   
                return False

    def isInt(self, possibleInt):
        return isinstance(possibleInt,int) or possibleInt.isdigit()

    def isFloat(self, possibleFloat):
        try:
            if float(possibleFloat):
                return True  
        except:
            return False 

    def isString(self, possibleString):
        return type(possibleString) == str
    
table = SemanticReader()
table.readCode('text2.txt')



