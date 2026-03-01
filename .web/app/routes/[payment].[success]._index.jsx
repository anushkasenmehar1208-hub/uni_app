import {Fragment,useCallback,useContext,useEffect} from "react"
import {Box as RadixThemesBox,Button as RadixThemesButton,Flex as RadixThemesFlex,Heading as RadixThemesHeading,Text as RadixThemesText} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {ReflexEvent} from "$/utils/state"
import {jsx} from "@emotion/react"




function Button_1cf85225a87eee61c7453844ca6d6b23 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_8552f88a33a715f92112f009d36a6cf6 = useCallback(((_e) => (addEvents([(ReflexEvent("_redirect", ({ ["path"] : "/", ["external"] : false, ["popup"] : false, ["replace"] : false }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{color:"green",css:({ ["background"] : "linear-gradient(90deg,#065f46,#10b981)", ["border"] : "none", ["color"] : "white", ["fontWeight"] : "700", ["cursor"] : "pointer" }),onClick:on_click_8552f88a33a715f92112f009d36a6cf6,size:"3"},"Go to App \u2192")
  )
}


export default function Component() {





  return (
    jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["background"] : "radial-gradient(circle at center, #001a0f 0%, #050505 100%)", ["minHeight"] : "100vh" })},jsx(RadixThemesFlex,{css:({ ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center", ["height"] : "100vh" })},jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",direction:"column",gap:"5"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "4rem" })},"\u2705"),jsx(RadixThemesHeading,{css:({ ["color"] : "white" }),size:"7"},"Payment Successful!"),jsx(RadixThemesText,{as:"p",css:({ ["color"] : "rgba(255,255,255,0.7)", ["textAlign"] : "center", ["maxWidth"] : "400px" })},"Your premium plan is now active. Enjoy unlimited learning!"),jsx(RadixThemesBox,{css:({ ["background"] : "rgba(255,215,0,0.08)", ["border"] : "1px solid rgba(255,215,0,0.2)", ["borderRadius"] : "12px", ["padding"] : "12px 20px", ["maxWidth"] : "420px" })},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "rgba(255,215,0,0.8)", ["fontSize"] : "0.82rem", ["textAlign"] : "center" })},"\u26a1 Note: If your premium access isn't reflected yet, please wait a few seconds and refresh.")),jsx(Button_1cf85225a87eee61c7453844ca6d6b23,{},)))),jsx("title",{},"Payment Successful"),jsx("meta",{content:"favicon.ico",property:"og:image"},))
  )
}