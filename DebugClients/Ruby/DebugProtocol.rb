# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

=begin edoc
File defining the debug protocol tokens
=end

# The address used for debugger/client communications.
DebugAddress = '127.0.0.1'

# The protocol "words".
RequestOK =             '>OK?<'
RequestEnv =            '>Environment<'
RequestCapabilities =   '>Capabilities<'
RequestLoad =           '>Load<'
RequestRun =            '>Run<'
RequestCoverage =       '>Coverage<'
RequestProfile =        '>Profile<'
RequestContinue =       '>Continue<'
RequestStep =           '>Step<'
RequestStepOver =       '>StepOver<'
RequestStepOut =        '>StepOut<'
RequestStepQuit =       '>StepQuit<'
RequestBreak =          '>Break<'
RequestBreakEnable =    '>EnableBreak<'
RequestBreakIgnore =    '>IgnoreBreak<'
RequestWatch =          '>Watch<'
RequestWatchEnable =    '>EnableWatch<'
RequestWatchIgnore =    '>IgnoreWatch<'
RequestVariables =      '>Variables<'
RequestVariable =       '>Variable<'
RequestSetFilter =      '>SetFilter<'
RequestEval =           '>Eval<'
RequestExec =           '>Exec<'
RequestShutdown =       '>Shutdown<'
RequestBanner =         '>Banner<'
RequestCompletion =     '>Completion<'
RequestUTPrepare =      '>UTPrepare<'
RequestUTRun =          '>UTRun<'
RequestUTStop =         '>UTStop<'

ResponseOK =            '>OK<'
ResponseCapabilities =  RequestCapabilities
ResponseContinue =      '>Continue<'
ResponseException =     '>Exception<'
ResponseSyntax =        '>SyntaxError<'
ResponseExit =          '>Exit<'
ResponseLine =          '>Line<'
ResponseRaw =           '>Raw<'
ResponseClearBreak =    '>ClearBreak<'
ResponseClearWatch =    '>ClearWatch<'
ResponseVariables =     RequestVariables
ResponseVariable =      RequestVariable
ResponseBanner =        RequestBanner
ResponseCompletion =    RequestCompletion
ResponseUTPrepared =    '>UTPrepared<'
ResponseUTStartTest =   '>UTStartTest<'
ResponseUTStopTest =    '>UTStopTest<'
ResponseUTTestFailed =  '>UTTestFailed<'
ResponseUTTestErrored = '>UTTestErrored<'
ResponseUTFinished =    '>UTFinished<'

PassiveStartup =        '>PassiveStartup<'

EOT = ">EOT<\n"
