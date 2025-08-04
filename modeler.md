You are to analyze the logic of a method or class in this project and generate a complete BPMN 2.0 process map of its behavior, with full module context awareness.

🧠 Goal:
- Output a valid `.bpmn` XML file that can be opened in https://bpmn.io.
- The file must reflect all tasks, decisions, user inputs, and automated flows — including predicted outcomes from decision points.

🔍 What to do:
1. If the method is part of a class/module, analyze the **entire module**, not just a single method.
2. Include external modules in the analysis:
   - Represent external modules in **different lanes** to distinguish them from the internal logic of the specified module.
3. Fully detail the flow:
   - ✅ Create a fully detailed **linear flow** for every step.
   - ❌ Do not use `<bpmn:subProcess>` nesting.
   - ❌ Do not include Pools or Lanes (except for external modules as separate lanes).

📌 Flow Clarity and Visual Style Rules:
- 🔁 Use `loopCharacteristics` for retryable actions (e.g., login attempts).
- 🔗 Use `messageFlow` for module-to-module triggers (e.g., login → session).
- 💬 Use `bpmn:textAnnotation` to clarify flag logic or gateway reasoning.
- ✅ For every `sequenceFlow`:
   - Assign a descriptive `name` (e.g., "Approved", "Retry", "Invalid Credentials").
   - **Style**:
     - Use labeled decision flows from `ExclusiveGateway` nodes.
     - Position labeled flows **clearly aligned** to reflect logic paths (e.g., left = no, right = yes).
- 🖍️ If supported, use flow **color hints or markers** to represent:
   - Critical paths (e.g., green).
   - Failures or rejections (e.g., red).
   - Re-attempt or retry (e.g., orange).

📄 Output Format:
- Valid BPMN 2.0 XML with:
  - `bpmn:definitions`, `bpmn:process`, `bpmndi:BPMNDiagram`.
  - All `BPMNShape` nodes must include `Bounds` (`x`, `y`, `width`, `height`).
  - All `BPMNEdge` and `messageFlow` elements must include `di:waypoint` coordinates.
  - No abstract IDs — all elements must be named clearly.
  - Include precise and detailed documentation for every sequence flow, task, and decision point.

🚫 Do not include:
- `<bpmndi:Style>`, `<custom:*>`, or `<bpmn:subProcess>`.
- Placeholder names like "Task 1", "Flow X".

📁 Save all generated files into the `bpmn` folder in the project.

📝 Output only the `.bpmn` XML — no markdown or explanation.
