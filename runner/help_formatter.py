""" Use our own modified help formatter to change the way argparse displays help
and to add the ability to display help on a single action"""

import sys, argparse

#I'm hacking the argparse helpFormatter class which can be found at
#https://cmssdt.cern.ch/SDT/doxygen/CMSSW_7_4_8/doc/html/dc/d81/RecoLuminosity_2LumiDB_2python_2argparse_8py_source.html

class Formatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        #changed to add commas between options, to stop options for being duplicated for each metavar, and to stop additional duplication when nargs="*"
        if not action.option_strings or action.nargs == 0:
            return super()._format_action_invocation(action)
        default = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default)

        if action.metavar and (action.nargs == "*" or action.nargs == "+"):
            if isinstance(action.metavar, str):
                args_string = "[{}]".format(action.metavar)
            else:
                args_string = " ".join(action.metavar)
        comma_append = ", " if len(action.option_strings)>1 else " "

        # ret = ", ".join(action.option_strings)
        # if args_string:
        #     ret += "\n" + " " * (self._current_indent+1) + args_string
        # return ret
        #
        # ret = ""
        # first=True
        # for op in action.option_strings:
        #     indent = self._current_indent
        #     if first:
        #         indent = 0
        #         first = False
        #     ret += " " * indent + op + comma_append + args_string + "\n"
        # return ret.rstrip()

        return comma_append.join(action.option_strings) + comma_append + args_string

    def add_arguments(self, actions):
        #changed to not display help for other actions if an action is passed in to --help
        #and to add the preceding --  or - to an action passed in without it
        if len(sys.argv)>2:
            try:
                sys.argv.remove("--help")
                sys.argv.insert(1, "--help")
            except ValueError:
                sys.argv.remove("-h")
                sys.argv.insert(1, "--help")
        if len(sys.argv)>2 and not sys.argv[2].startswith("-"):
            if len(sys.argv[2])==1:
                sys.argv[2] = "-"+sys.argv[2]
            else:
                sys.argv[2] = "--"+sys.argv[2]

        for action in actions:
            if len(sys.argv)>2:
                if sys.argv[2] in action.option_strings:
                    self.add_argument(action)
            else:
                self.add_argument(action)

    def add_usage(self, usage, actions, groups, prefix=None):
        #changed to only display usage if an action has not been passed in to --help
        if len(sys.argv)<=2:
            args = usage, actions, groups, prefix
            self._add_item(self._format_usage, args)

    def start_section(self, heading):
        #changed to only display section heading if an action has not been passed in to --help
        if (len(sys.argv)>2):
            heading = None
        self._indent()
        section = self._Section(self, self._current_section, heading)
        self._add_item(section.format_help, [])
        self._current_section = section
