import {Fragment,useCallback,useContext,useEffect} from "react"
import {Box as RadixThemesBox,Button as RadixThemesButton,Flex as RadixThemesFlex,Heading as RadixThemesHeading,Text as RadixThemesText} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {ReflexEvent} from "$/utils/state"
import {jsx} from "@emotion/react"




function Button_5f2c27b433c0017273c1f7a201cfb3f2 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_8552f88a33a715f92112f009d36a6cf6 = useCallback(((_e) => (addEvents([(ReflexEvent("_redirect", ({ ["path"] : "/", ["external"] : false, ["popup"] : false, ["replace"] : false }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{color:"green",onClick:on_click_8552f88a33a715f92112f009d36a6cf6,size:"3",variant:"outline"},"Back to App")
  )
}


export default function Component() {





  return (
    jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["background"] : "radial-gradient(circle at center, #1a0000 0%, #050505 100%)", ["minHeight"] : "100vh" })},jsx(RadixThemesFlex,{css:({ ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center", ["height"] : "100vh" })},jsx(RadixThemesFlex,{align:"center",className:"rx-Stack",direction:"column",gap:"5"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "4rem" })},"\u274c"),jsx(RadixThemesHeading,{css:({ ["color"] : "white" }),size:"7"},"Payment Cancelled"),jsx(RadixThemesText,{as:"p",css:({ ["color"] : "rgba(255,255,255,0.7)", ["textAlign"] : "center" })},"No charges were made. You can try again anytime."),jsx(Button_5f2c27b433c0017273c1f7a201cfb3f2,{},)))),jsx("title",{},"Payment Cancelled"),jsx("meta",{content:"favicon.ico",property:"og:image"},))
  )
}