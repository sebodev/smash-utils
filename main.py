import sys
import runner.vars

if runner.vars.installed != "True":
    if "--setup" not in sys.argv:
        print("Hello matey, it looks like this is your first time running smash-utils. Let me pass you on over to the installer")
    import runner.setup
    runner.setup.main()

else:
    import runner.runner
