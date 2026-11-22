import streamlit as st
import langchain_helper as hl

st.title("Wikipedia + Calculator Agent")

question = st.text_input(
    "Ask something, e.g. When was Allama Iqbal born and how many years ago was that?"
)
verbose = st.checkbox("Verbose (show the agent's steps)", value=True)

if st.button("Ask") and question:
    with st.spinner("Thinking..."):
        answer, steps = hl.ask_agent(question, verbose=verbose)

    st.subheader("Answer")
    st.write(answer)

    if verbose:
        with st.expander("Agent steps", expanded=True):
            for i, msg in enumerate(steps, 1):
                if msg.type == "human":
                    st.markdown(f"**{i}. Question:** {msg.content}")
                elif msg.type == "ai" and msg.tool_calls:
                    for call in msg.tool_calls:
                        st.markdown(f"**{i}. Calling tool `{call['name']}`** with `{call['args']}`")
                elif msg.type == "tool":
                    st.markdown(f"**{i}. Result from `{msg.name}`:**")
                    st.code(msg.content[:800], language=None)
                else:
                    st.markdown(f"**{i}. Final answer:** {msg.content}")