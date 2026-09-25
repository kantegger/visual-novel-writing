# VNMD-0.1: Optional Path-Checking Format in This Package

VNMD is not a game engine, part of the Agent Skills standard, or a Ren'Py / ink converter. Ordinary manuscripts do not need it. Use it only when deterministic path extraction is needed and the project allows it. Even if an existing manuscript uses a similar :: syntax, check this guide first; do not assume compatibility.

## Input

One UTF-8 script and one JSON state file. Python 3.10+ is required; only the standard library is used. Prose may be in any language. IDs use English letters, digits, and underscores, and cannot begin with a digit.

Text before ::scene does not enter a player path. Every scene must end with an explicit ::goto or ::ending; the next scene is not entered automatically based on file order. Put author appendices in another file instead of expecting the parser to recognize them after the final scene.

```text
::scene START
## Before the Rain Stops
Prose goes here.
::choice ASK
::option speak | Ask whether she is willing to stay.
::set asked = true
Write the actual dialogue and response.
::option wait | Take her umbrella first.
Write a different concrete action.
::endchoice
::if asked
Prose corresponding to what actually happened.
::else
Prose for a path that did not ask.
::endif
::goto LAST

::scene LAST
Ending prose.
::ending FINISH
```

State file:

```json
{
  "format": "vnmd-0.1",
  "entry": "START",
  "defaults": {"asked": false},
  "invariants": []
}
```

## Supported directives

| Directive | Behavior |
|---|---|
| ::scene ID | Scene entry; ID must be unique in the whole script |
| ::choice ID / ::endchoice | Mutually exclusive choice; choice ID must be unique in the whole script |
| ::option ID [if expr] \| label | Option in the current choice; option ID must be unique within that choice |
| ::if expr / ::elif expr / ::else / ::endif | Nestable condition |
| ::set variable = expr | Assign a value only on the currently executed branch |
| ::goto ID | Immediately leave the current nested block and scene, then jump to the target |
| ::ending ID | Immediately end this path; subsequent text is not read |
| [CUE: single-line note] | Remove this entire line from executable reading text |
| <!-- single-line author note --> | Remove this entire line from executable reading text |

Unsupported: code fences inside prose, multiline cue or HTML comments, variable interpolation, macros, functions, arrays or object values, engine commands, automatic save/load, and arithmetic expressions. Unsupported directives or code fences produce an error; unknown structures are not silently deleted.

## Expressions and state

Allowed scalar values are limited to strings, booleans, finite numbers, and null; variable names; and, or, not; ==, !=, <, <=, >, >=; parentheses; and unary plus or minus before a number. There is no eval, function call, property access, indexing, or arbitrary Python execution. The pipe character in an option line separates the label; it cannot appear inside the condition expression. Conditions must evaluate to booleans; a non-empty string is not treated as true.

Each run starts from defaults. Runs do not inherit implicit values from previous endings. Declare variables before using them; an undeclared variable is reported during static checking even if it appears only in an unchosen branch.

Use domains to declare an enumeration, for example: "cup": ["intact", "broken"]. Without a declared domain, assigned values must have the same type as the initial value. Equality and domain checks are type-sensitive: true, 1, and 1.0 are not equal values, though ordered numeric comparisons allow integers and floats. To convert a null variable to a string, explicitly list all allowed values in its domain; a null variable without a domain must remain null.

Each invariants entry has the form {"id":"unique_name","expr":"boolean expression"}. Check invariants in the initial state and after every assignment. Intermediate states must satisfy them too, so dependent assignments may need a deliberate order. Invariants check only rules the author has encoded; they cannot detect prose that says “the cup is intact again” when a variable says otherwise.

## Three commands

Run these from the skill root. From another working directory, use the script's full path. On Windows, the interpreter may be named py; substitute it for python.

```bash
python scripts/vnmd.py lint examples/umbrella.vnm.md --state examples/umbrella.state.json

python scripts/vnmd.py trace examples/umbrella.vnm.md --state examples/umbrella.state.json --choices examples/umbrella.path.json --out umbrella-reading.md --record umbrella-trace.json

python scripts/vnmd.py sample examples/umbrella.vnm.md --state examples/umbrella.state.json --runs 200 --seed 17 --out umbrella-sample.json
```

lint checks syntax, paired markers, IDs, variables, target existence, constant domains, and conservative reachability that ignores conditions. A scene that might be unreachable and a structurally unreachable scene are warnings; this does not prove conditional reachability.

trace requires a decision at nodes with multiple available options; it may follow the only available option automatically. It never silently picks the first branch. A path file value may be one option ID or a list of IDs for repeated visits to the same node. Unavailable, missing, or unused decisions are errors. The output removes unchosen branches, state, and cues for a human path read; it is not UI rendering.

sample chooses among currently available options with a fixed random seed, then reports success or failure, visited scenes / options / endings, and omissions. It includes at most the first 20 failure reproductions and one representative path per ending. Reaching every ending does not cover every state combination and says nothing about prose, character, facts, or emotion.

By default, all three commands write to stdout. The --out option names a generated file and refuses to overwrite an existing file; only an explicit --force replaces generated output. Even with --force, inputs—the script, state, or path files—are never overwritten. trace --record can write a separate execution record; its output paths must differ. Every command has --max-steps (default 10000) to stop an endless loop.

## Validation boundaries

These checks cannot automatically detect mind-reading in prose, reversed time, reset emotions, abilities that were never established, opacity, or dullness. Only explicit variables and assertions can be executed. The program does not call external models or networks, compile a game, or validate audiovisuals, voice, saving/loading, or device adaptation.

Unit tests for the script are not writing-quality tests for the skill. A validation report should include the actual inputs, command, random seed, coverage, and untested scope.
