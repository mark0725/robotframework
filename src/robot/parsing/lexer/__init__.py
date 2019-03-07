#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from __future__ import print_function   # TODO: Remove once "main" is removed

from .context import TestCaseFileContext
from .lexers import TestCaseFileLexer
from .splitter import Splitter
from .tokens import Token


class RobotFrameworkLexer(object):

    def __init__(self, data_only=False, lexer=None):
        self.lexer = lexer or TestCaseFileLexer()
        self.statements = []
        self._data_only = data_only

    def input(self, content):
        for statement in Splitter().split(content, data_only=self._data_only):
            self.statements.append(statement)
            if self._data_only:
                data = statement[:]
            else:
                data = [t for t in statement if t.type == t.DATA]
            self.lexer.input(data)

    def get_tokens(self):
        self.lexer.lex(TestCaseFileContext())
        if self._data_only:
            # TODO: Should whole statement be ignored if there's ERROR?
            ignore = {Token.IGNORE, Token.COMMENTS_HEADER, Token.COMMENT,
                      Token.ERROR, Token.OLD_FOR_INDENT}
        else:
            ignore = {Token.IGNORE}
        for statement in self._handle_old_for(self.statements):
            for token in statement:
                if token.type not in ignore:
                    yield token
            yield Token(Token.EOS,
                        lineno=token.lineno,
                        columnno=token.columnno + len(token.value))

    def _handle_old_for(self, statements):
        end_statement = [Token(Token.END)]
        old_for = False
        for statement in statements:
            marker = self._get_first_data_token(statement)
            if marker:
                if marker.type == Token.OLD_FOR_INDENT:
                    old_for = True
                elif old_for:
                    if marker.type != Token.END:
                        yield end_statement
                    old_for = False
            yield statement
        if old_for:
            yield end_statement

    def _get_first_data_token(self, statement):
        for token in statement:
            if token.type not in Token.NON_DATA_TOKENS:
                return token
        return None


# TODO: Remove when integrated...
if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        data_only = False
        formatter = str
        end = ''
        ignore = ()
    else:
        data_only = True
        formatter = repr
        end = '\n'
        ignore = (Token.EOS,)
    lxr = RobotFrameworkLexer(data_only=data_only)
    with open(sys.argv[1]) as f:
        lxr.input(f.read())
    for token in lxr.get_tokens():
        if token.type not in ignore:
            print(formatter(token), end=end)
