"""
The TrafficDom reporting design system — VENDORED, DO NOT EDIT.

Generated from the Growth Engine at fingerprint 0ff253c55ea61236.
Regenerate with:

    python3 -m growth_engine design --export <this file>

One visual identity for every TrafficDom report. Editing this copy makes the two
reports diverge silently, which is the one failure this file exists to prevent —
a test in this repository hashes it against the fingerprint above and fails if it
has been touched.

To change the design, change it in the Growth Engine and re-export. To change
what THIS report says, edit the report — the components take labels and data,
and none of the wording is in here.
"""

DESIGN_FINGERPRINT = "0ff253c55ea61236"

"""
The heading typeface, carried in the page rather than fetched by it.

TrafficDom reports are one file each. They open with no network, survive being
e-mailed and archived, and a test in every renderer asserts the page requests
nothing from anywhere — which rules out a stylesheet link to a font host, and
would rule out a web font entirely if the bytes could not travel with the page.

So they travel with the page. Belanosima's four Google Fonts subsets are
embedded below as base64 woff2 and emitted as ``@font-face`` rules whose ``src``
is a ``data:`` URI. Nothing resolves off-document: a data URI is the font, not a
reference to it, and the page keeps its guarantee exactly as before.

Four faces, ~42 KB of woff2 before encoding: weights 400 and 600, each in the
latin and latin-ext subsets. latin-ext is 2.7 KB apiece and is what carries the
diacritics a Czech or Polish client's name needs, so it is not an optional
extra.

``unicode-range`` is kept from the upstream CSS. A browser downloads nothing
here — the bytes are already present — but the ranges still tell it which face
to reach for per character, which is what keeps the two subsets from fighting.

BELANOSIMA
Designed by Ania Kruk, released under the SIL Open Font License 1.1, which
permits embedding in a document like this one. The attribution travels in
``LICENCE`` below and is emitted as a CSS comment beside the faces, so the page
carries it wherever it ends up.

The pointer to the licence text is written without a scheme, deliberately. Two
source scanners in this repository refuse a real domain anywhere in the core,
because that is how a client's address would get committed by accident. A
font licence is not a client address, but the scanners cannot tell the
difference and should not have to learn: dropping four characters is cheaper
than an exemption, and scripts.sil.org/OFL is no harder to reach for it.
"""

#: SIL OFL 1.1 attribution, emitted with the faces. Short by design: the full
#: text lives at the pointer, and this states authorship and licence, which is
#: what the licence asks an embedding document to preserve.
LICENCE = ("Belanosima by Ania Kruk. Licensed under the SIL Open Font "
           "License 1.1 — scripts.sil.org/OFL")

#: The family name the design system asks for.
FAMILY = "Belanosima"

FACES = (
    # latin, weight 400 — 18,116 bytes of woff2
    ("400",
     "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
     "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"
     ),
    # latin-ext, weight 400 — 2,788 bytes of woff2
    ("400",
     "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF",
     "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"
     "icD4A4LmF9Bk6T1jAwAAAA=="
     ),
    # latin, weight 600 — 18,412 bytes of woff2
    ("600",
     "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
     "d09GMgABAAAAAEfsAAwAAAAAfnwAAEeZAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAABmAAhGQRCAqB3ySBuDgLg0wA"
     "ATYCJAOHFAQgBYRkB4V1DAcbcWhFR3XYOIAGZvEOoyiZrAcQRbkiNcH/hwNuDJUc2HuhaAin7Dgd15J2a0PM5tYu"
     "pFOx8gmDmf4O3ivEnwhiCpketzf0TRtphlYgr596x8wfobFPcnl42h/fuTNvQUcpAkxy2rQVRBTrhrIO6X/XhRJm"
     "eH6bvQ8t9WmjQMVAJd4HEZOQEiswGrsWbjMWaW1zFa5vecu8WkRcra92UdNsJSQdpLzz3TdXYF/UKbqkaTL9mxjw"
     "d1WEh/7vn/2e3zn5x7MMA8Asw0xaD9+dBlc5+v+jzk/n/havgWNYf4exw3aEW8vrXY/kjvEqW7Zlc5ywkw/IT1Kg"
     "BATmmQsAL7sFSlT5ixaoDNP+1/L9lmcWvSgQKTpM1yVXB4ASlcH99tPEJqrbHY/o+So/UKzGir6SBYABg/+fqvnt"
     "kNpAx1w6d3bRxcqli9ZNA9w3wANmAIEaMIGgvFxI2kBuJB1FB0LU8QFp5yrFLpc+rvZQDjH8X8am6H776//3a6b9"
     "P7svwP+ogL+0qbuLsO14QqE6HZ+84O5mC8gH5ApAtpI9Aate3BGoysqcE/WWSN2cbE84VSFrMjT9QwNk75glSHa7"
     "yVykOFY9OIhYYyhxrJWfl2xVxW0Y8ZNxJECU7ojB/9dQ5R+Ziwi0uDEQiBHty+R7upNzROrYOqUWy2VyS0De6e84"
     "52vJHPHA0Hey8yl0oVVubPwAAqBCvAEYDCAx+N1PjYSnEdLS1ji+8Ticf/Rokab7H0ZHRl7MB/mokJxz68Fvvu6+"
     "3r5iX4mv1tfou3hlqJgj5v//PxhMTmtdKCKdugAufPV19fW8emSpSc3rwxcqnsD/3g/lv/vv77+r/y4AdZfux9yt"
     "ViM9ytOfGtXjgv0x4U0XugXEObU4jsAE+P/QM8OWGbXfGecst8568xyy2CZjVlhkwgnHHDfuLASVCzomLh4+AQ+e"
     "vHjzIRJMKlSYcDIYFbUIkdaYb61vrPSMlp5BAjO7JMlSZMmWI5dDvnJOlarUqNWkWYtWHVb5ymqn7DFir8/tc9DX"
     "Lnjqok6bnXbYJc996aQBgx7pdt4Cj/XrMmmO2eZaiggHj4yAhIKGgwXF5k7IlRsGXwHE/ATyd4QEJKegpBGiWqwo"
     "0eLFiKNjlMjCyiZTmnQZTPIUK1CoVJGjSjSqU69BmwrtgpTZaIPtdtgGgZT/dQLQPKVKb0XbyvDvyui/Sqqpx+e5"
     "8uG4YjA8YEHmKUJFbAIuCRyqjHJsEhGVjT2fmeGkA0MJV8RVr1vanrch7MSWmZ0qYoxF+AzAWQQEdmI680yMsZCc"
     "JESATuMJO/GAiMgPEQ7GTptMkuHWfxtQVROvtbQIojHU7jS1MiZV4J8qyTHy2Do63cgVsfypIa5aWkRobGR5abSK"
     "GMQoo7DCUZkMtdEDqXFxzFg6m00XZQgKVSwUo9GiqWgIQ81QsMKicuQRBGVeWrxSwuLQtQyGh9EUik8I5AZI6HQp"
     "2w2LDwwUK/xFSnJgjIKcLkI5KOqNquB9Me6i1qiUTg/hstlMbzFqT5TLw8N6uvJQaUjuP8jVTejq6urm5ppBzkCr"
     "qeTWgroQNJGO0pl0uTyILhGgISiKOngl9PgshoAv53H8XESQz3RHUTGdznPzZ9H9NUw6XejO+wI0bpFi+6JClE0P"
     "4vj8Pn/3U/o+kTmOoFr0jevliaws69IP0EwwShFrLuEReuaKGYyE0TbYeI8iDTjnDCCzD3OpnEriGwMZv6c/w2ZA"
     "9s2YFAZfYwnomhzriomsGYB0wlRA97sXIcvYjxrf8IESnAkTgpYIHo01iVkXkOZD+AoBwVnIx9WUYWRXCNbpaGdv"
     "VwewT1Vqo/vXwPXZ2OJfbun1/2OxQQLffhM2iEMVQhcTGM9PJWX2oaCUd/jTBXT+oH5Xmwf+3ytyPpQLQSIVv70B"
     "E4+XbksBS9NZXx3yeaAZjkgWIsaqdgcl88QVlJmFz5xCT0pY/M+W5WKtehQVcbPdOFXfDaoH2I20sZPazh6cMd6n"
     "9ppijQZ9DV11BfzhHAd324hpk9h45L2qdUBnul2yj2HD4560znI5VdIJuxTP7UP0ZhED809b+vqJnorraX20PDEq"
     "BGxGb0heRy9zxQHwm6ex8kIYNPJefxnIdLRCsZtFu6ZV79a4yznTz5ehAZ+B0oCwi9Ogq6ZtE9jOEq0WT9PHRKwl"
     "8xLLZowusXR6oK67ZOjwCTr+oVbkuGCKRTQEdEh6OPgnWDqKAmNUaJP8RgcME1IsxlUXBLPH+zcd1lgU2UEy0UPW"
     "v0JfKSwmNAxytnjFPayKCbBeDnI1ltWlYO5ks4cABPIjyaLq4un9Q0qqthyiW4iZE0ROwmgfmr6VrJWLKcSiRd8g"
     "qn6Dbnox0OFIxCploB9cqcqKYjWtboCKryT9ci9W2sw2hj/5INFT1vbk9a9yPgx+zKLiBGyrn6g9QYJBPy3GUlC6"
     "wzcKNPT7m/8bUCTx47HB3+qHkp/hJsSnmzg3h1Rmx7BkSZwpzp2Nw20iprefF5g3m7YepQmP2BBc/RNTHLVTZjip"
     "1cPp1rATaYx10o+eowa0d2HzhcyHN81qkWDaoGCpZHz6lspKKYshBuRCQ1+8MwALgDrMg8k+7Gb3quW53QwiCKIp"
     "HHanqKtDIYZ0pgH8kZjtys/dFc22kvL0bJPpDO3aLKrtsSdmnRgj1b7M41cIw431iUp4xFPeY3qUTPBSxc7y/rmx"
     "LjjtxURoaWf4f/2l5pkX/VwDtc3g9iHhnBlUVuHnKW4s8qYhLR0NnjGbdollz5e7Ez0iYqnnaYMGw41jIHaYzz1r"
     "JS7MaTsBYu9ktQwVN0u9OR+PRWKEe+Qhg6t87LchKtPi0KUH0BJyTx3bIsOCbkAlXCIQ1JGWgpIdGdt0nN5/Q4Hb"
     "gvmX0Qr7cdy4zHcTxMwuNKoiMpVop83ux1qpjcXq+PlQEi4Sa9AWepNoSLt3RiQVMQpxoM0mu/SzWkrKbPFslkbC"
     "Zi9TSAeFwIB9XdbZ0vq2f3UXbM0Zjl4mQ/LoTlTnMYV2MwVDGtwYUwE1GIZQX5NNKpwecq3+JrsMMKy8OrX9uyoq"
     "enus9jG1wyLUHRzA9lG9YN/H4hBabFonMlTY1fwcbqb9hRYfWsvvz8HMviJgTV/eqWmGXba+E1g/CCXeEW218/KA"
     "NdcCk4/GU3RT+DPQg4HYWaz+Iw5jzeBrli4MEcFDKFl1QFSW3P25AEM1Hb/dn7FrM3e/sJ2V+LgKyGCzKI3M/oKg"
     "PuxpAcBOO71mtnuIlQuryJY1uYXJexVVOOQlalXNq5rX2KARuPuoRXuIt5Pktm3pk9rlLnyCZBjL46jbqA8hUK1E"
     "wwTs0nWNSFqVTXRm64PcV2oeQS1au2slzvHcheoVYfQH+j+eROFdrgRA2c/A9of1TQGwmKshPXHLPAfc7eKm32uZ"
     "l58uNcZhx3Y7gqsXtCDVwSCxpbwyzgKEO2UPYh9qbshlDYIxhSycthGAjHhGcknNVKyPzTEVvtNV7JBvJA/gKwBs"
     "7b9OxASd8Hckd+HqVA3MnjpynqtW4y7E6Tpi4cKGE1kovlIfMqUQtSWvM1ZI1Q51dwviaCrsfVeqjvI6Xf6uNNfd"
     "CCREbhbLJgs31claYyPEhcMuh3g0V72J1fsnNHmG11UyCJjGeK6rGYOKuSYBpJomacbRH8T5QXYcInEjeaPCfN2o"
     "qWI7jkCaNSti79bAPPk+nmdFeI3OgKRkIvi8ytXAIry/ctbW7vxjbc9JAVGKHgPqjZFX6L2mTlLHXm9Hdu3LgIHc"
     "KjmW+EkcE5ve0R4Hz8kt5K+SFJtZWJ4uhFu+ChVvKqkRaFf/1/UjitgNGkGEdWL7V5OxIzTZvtvaOwieDSOCvKzY"
     "ePB3UQF93mMnVLioh2nEOQrwhgOVNg32dA/B90Z2qDe+myHfW3jB2f32HTvEoitUjyWeto4KHLn3vhv2Ew6aKiP7"
     "xT/dhXkcNuy83D3OANtD26i/ojeliRfh1fSJCK9jAHwFkIEGhBlps7vsdWzgNWTa0NXSVD1riJzmLIPwwrdyB09m"
     "1zCPGe+ModGYlt+7PgD8CPRtFuADSp7OSL0QilVNgHYuhajfmBeshMJYF9hi12hELhCAhWqqIovPWivRflyFip2u"
     "SdfPoF2iDwV7vYhJ9TBJnGt6EU2hOJ+w0vjvO/oK7/z7bfufBXATEykszwecrFgtzHW7Yl2fCKUM4smhmmaJCfAT"
     "RbGe2x8hD70NxMa9ZvpRlyrxDDueGSAqQ24U1AFuR8295asbBxG+hDdujsBynJcZAM49QF4O/QSOU684aN/k/TaU"
     "tqd9wHTEFSXb31sJpS3vWC2WaXAX2/KnGIibRODGX+XUSbIje0K14ULChCyHPpMVGJwUm5CGZ11WMqF3/CCmBzls"
     "2QEMy14bRoEW2RpqQWh0zkekscEt4P7jcvMcQa5SVUatQbSX3vQAYh9xt04jCr2KJb8iC9zR1TyLzYQWnShb3F1t"
     "VB+FWFeaZktzTyTqDpKInhg9Ro+rBKwpPamvD8svKGPwKljpJEuJiDq3dsRwVjZ3F8lxI6wCbUw9UWoG8emmFXVB"
     "SmEQ6wTIqhbLLfzMAW4c5BiJFHirJSLNfV2Au99RGa/ijWtIxuA9BWeaGNg7+liRswq3+z3vCslUF1og4rSypoIr"
     "5NSrlrLj3iYp3bj7J3RQN9mhfMP7deaNbKvFBzlrOqC4n4Ub2DFPdMPPtQijd8zpG33lroKvcN0sJaJOVprFIY6g"
     "AntHifoJHeYrLphlXIJgS1TeK6TU0y0kmYS3v3mLeJa162ZedhDTz/vDQaTr3UnNTXuswrZWMH75jMZC71PHnvba"
     "jVNRZBP3x0KpKpV0ocm82dbpPtFS96GLCffhPGoDCUZUn80J7qPO1/k3ZzX9BJ2MvU0bohoQxNK0JSIFOqvnqwcy"
     "ep/nVJiZAftM55STl5ls9G0wj+XUQjy/ksX3vi+h2mCeej4SvpaMH0sjv2Sz00oG+8kHUbUeNmzjg5etf37+PWLq"
     "FQxQ4WFQk2I/pax+Xns56GItT6LME0m4+7c4dAqa7AlPpiS9hWTSsb4IXdXqU2PRu+GJUzrxcOqNDjQ/avRkrV5t"
     "Jt8GqrVO1MaWZh/Ek5Un2Q1mPooxz7VRl29/4Ut6vuERHN906ST6pRKAgET1Ir9ho20IYM78Fv422yEiUp5SZJ6R"
     "nF4JIdL31LHUBOd6xNyX0APwwJ83Zc6HEHAKxeArZaXaP0x9dGwSt1UXorY0O/3UWhJQvVEM9mCUSxYKH5fLlpYu"
     "unUtt+8g2iijcdVKKkMcJMno7pLqsieXOHS+hkzhpkRG9kKta7yl7sHTC8cfIGsLc4HHMsO0V6d4znBDoLkuZazV"
     "SZn+/pa4M2shQKeyGPSSU378DhWBNz9vEXO8555FnS+CFURRRywH4CSGQ3VNdtTDuoFxNbKJxAl60y0+43yY3xcZ"
     "3hvPgr/Nj6ypY14zzVNSzIEFkXkgKrFvfQDhNt59PRSQeTL/7Ab8uTkZ2ErLIr/AKweuT0ISPp8Xn3HQV1lliAG3"
     "yMHHCWL++9lSS5WFj6rKPVY+l0ITkVu4sjICPk4+Uz6JL6A83ecVzhlVe0akXvMVYjI/HSWmx3uwLLu3IDK9hCec"
     "5in0lKtHzELaLpTZ3Lk6fBbhNLcD9GkWq5Z0X8Loo4k3z/vlagAh07a/NiW/twL3jcrQ/WIy+7jVAI1eSfj+qBv0"
     "c7XX4HH06PCoqrTB7UOTKdvURPT3vmgWjYxvJ2GoraHhjUCixBtcQlGGN3GafMew2iGwN2/ETGtTM2WUdVUWrkmu"
     "VwI+yzcs3aA61bzrayuU+VHNw53DsGQLyNxvRmcKtYi+70DMPdRT2OFyEkeSXNIR+UdlWXOpkd+JxtWCGatp30X1"
     "nFfW7aPwvQ8Z1Etqm1foNlrW+IBEfXSuND3COSthhGeV3XRgB0l6TTechRy0/jCJ7Z5PRlfjiihV3f5R8Gtq7fpT"
     "E1RssaDM3F05PREpFrKiOOsmD0hOi1oqmSJgYeif5IFaUI9C5npTFvHEobZM7YCHtXq5j4nprVghgqSqWCzgtiCH"
     "OArfH2ohvNFHCzuhFTlYNhg/0YKX4q8/WhN7B9zhhoiQSGyVw6CMOP0c6sLntGcDkuo1paMOWN6zUxehEYFE/MhI"
     "y8aGpfx78UVb6AJZFR39ZRTfibwLxKGK/nJTC2nYUTmeHX8RpWHx/Pea+zpiLdycsGJAYz1G4lF4BliMrDX/fUzt"
     "2cvD0iSMgtCDBRMSniPac0g5gBWbVddd8cE7LvLTJU319vxb1cbSddyX3iJCfeSMtTROwivH2ItquWIbqMvCjfpt"
     "PKF8RmaOzwSm0/6hqLAXtXIde1F+jgP7ZRNnJOSGmOTmHIpvhxa8DyKgiPGilgWK3AimjuWMZjjsDS3uK36b7Mio"
     "4T7WkoHHdHP9yp7xRsCcNd/irIb3gvH1X8Cn8acrBUeGDn9zCdbsHaXw7kkFuUVuya6Ibk0YhTWjLeWJ9W6G9ihP"
     "4uJJ5Oelu1yWQ9iyvnxetkOPMj7EHZ4fp2YaoCra5OQL4vDmLWUvENhgjjnpdmZDeHqx3Yn11aDB2b5eVDaeS5fr"
     "ak731EOuBASAJ5cEylbtLnwAPD3kRxoj3pApoWePlsDpBolM9HJPRbFIH2ePiFnYaMh5D+n2Y9wwrODROmbI1jtd"
     "JlODqncpozLUOv70IvNKpKN3d+ENlXdWNzMnOsgfOLpXnJI+Nb6KhyFDDIEBeqEIBKXUTpBqanebqjOKnh4hCPy3"
     "uIIcMLm/Cx0tVUNuwlOraVPNXQeDiLIjId5C3Vh92H2Em3YSoWed1cbpvTJ/rgzgcfbHqWngYfsvtWlSoqeIwyl+"
     "Lka51Kj3Bh5SHOKkGJAlKsP9LIJ5RNgLWGPnmAa5yJkzP1Od5gbW0EuksYEzIWo0r2OLmRX4wYE17WjerO6+mnCH"
     "C60dZHsTtVMbaSiqN8JqPtkeMxYDjWQ1jAvsdw9xK+Mi00ksrJEgg42lHSxbWZZetBL/bd4L7lEMKkXgRDmT9igV"
     "JbO5yUkjYKvr8+fxd9OWxFo9D+4XZ4e2B2tFKWud4C9/tWhRZwCftEJBQ+igjIRBA8tqBj9eOWP3DV7d9UYDCoCu"
     "Zhuo3PDgmqrb/94YHp//r4LlUCcfzOXXfTWSCIZYrEzY8ZBO+eUj+psiVJNVPrdEAMfaLN9xNQG1y/H3qLzNKoMQ"
     "MbVacoLlBMQS5d1Vvi7oBSCiN1vKni+ktWryTu6bln3KvHp+bOJKC9VFEz0FT3Fizul9Ux21WJYymnA+28CTNwe5"
     "5VJtLgNUM8AjJ+afSFyR3xfH/fGXSwJD+GyB3k2PzQbN9MM17fu/rW76vGD8YFjx6PeehzG1l5RBjXAXyU0sViRS"
     "Hcq8jhN9HrYkZBkh7AYjCKlVsViFcpF7hAtd6q2CRyB8wGZ7UC1u2n73v71i0Pt7fPdUAXJAkQr7OvuEz6bkyvl1"
     "BYlLTBHKTiJpqaJI1b20vbd447qSS8HVCKZS4WsJSBPytLkZeYI0EfC1gjMqu1GtcYTJRsktmlUSSQHLIFeqLdIy"
     "cuBwBGjQAN1PI5zgBoePPiD5MzLH+9MINuEW+1h7fNJ+9/Iyo+TEneKXylRs8hqT7J7g7/C12Qp+Y3ON8gKFpmZx"
     "u3Vfca350HhLh7Za/N9kAZiEKgxfiUeakRetLcgLpBmPr8RUcPPb6s1f236/dUZp23h5va36+K395xqj9i2qnrIf"
     "1wfIAcUYTMdUvj4sCuoqVvzKRsFFFN2GYacxbBuKgssomyYXBSBdahVWAzEVrpaANA8sfeoJfibSdPNiJAFHpPNF"
     "cjYb/QplH4UwErREYtjRtX47+L59rXyW4po1Y6/wv/KZmqWBi3nYam7Wje1d/25tWjjRGr0KXe5rvcNmE7lG9xyB"
     "OaiYxHPhz5ePjwxvO3B+F8NKzKRfQMEAyr4K4UIIf4DwMO4gA5cHsoijcKJQnIh7YZUK8mX6YCRHCuzIyiQU/QlF"
     "k5CVICkEyQlWynm90ieGp2f0yHXFcMlEkAbWp5cfIR2sB2lEXDLmmusByAnFGORBbDPOtnnyHkyVJ/EPCBR+W4tc"
     "r+WER9HdyeEwAGcl8Glcd8MgFulmk0hX2gWnkKknIXSD2Bp8NPDkj8qVAUiKBKRtSifaySRlX/SWKyGDPfscO4IZ"
     "/OuuRI+cRbZ3Q0RCRLZjoHq8ZIHJua7mHkP4I6oV8taGJ7Ro09u2RqVxr5LI7jjcXgjdZ82xKhU24aotH8KDoO5g"
     "GIp+75nrxvMkIkiCnwozTqvP0yRUqQn1RKQed7chnBLKoRVx2TPmDSY1ViY3rnic1ITqS32qyaRqbUrzek1K97Zf"
     "UqZuIpJOkKadasDdRxpIhPoIFRR4aoK0UhowgHmIAedNJt3mJA8soycNElN6Vv6e1s09TSJ74CKRVoqnVBuk8QQ5"
     "H0MJeZYl3Z+N7Fu2aqipyFvZSST7EtuQ79q3QejZoPiHe9wMiP/Qid0xZAqp4vGBndPuHVMOEShswkZg2DgguALB"
     "+Z8noSwRgeXSkkrS0a//7hgf/79j/nIteWS4lnDii/9ax5b903r0q0rixT+SmiymTtFcfYH+0Jzemsp5vabP84sS"
     "Dw13g6TxHXSfao3KWrWPxhldTcOZk5yZb2aOVBGPfvlP29Ksg+GWUJGSQMs9zGdw80hnbtXZL+raBTSiKqUm87uh"
     "JU7yoSt/dy4t26nKUOiJdMeRTze13MaBhsGr/Mp5ZrWjYnaHcc/KU2aY45zZFbc3J4JVk14/8A0bZHEEMlAkQ9EO"
     "jxw3bx8WWeSqxk7TL57JUlMmvKqen+ynbNjQz3h+zrt2ZZTg9EXGJKYWykgMTy/XXI9cFFWCCiWK/olhjzHsT7T/"
     "BSg5XVoCTpdmSxtOlLV/1trWve+Ms4mjWPV9bZ/2vlId6Kw5vWDryLf/dqy7gbJxqRDyMFUEvoGENCCPGhuRh0gD"
     "Cd8wzXRFWRQUkxRBbQziGeqNCZeB4wDwHFwY6ElOpfPP7vonf+69YyRPMnKP70JOcg8UYyoNvpmENCNPmm/ibpDx"
     "jREYJoLTspodecXV2fkna4Hl0nAV6djX/3SML/2v69jlasrwfCexqMKvVV5BphgUOhtL8CfrV5/vBUwExRF1JPEE"
     "LMjYaf1vjz5FxIesz8wzHpjTVVU9p0d/IL9At3ew10mOCsrSbugggADi6A5ayfJHxxc1v59qmSQRFKbE8pSq6JT5"
     "PTSmwJWlcRP8dvo7aULWonCjmapis7OQrVkjYelLVsW+ty8xzWk2J7clDQPHgTwQ7rSStrIsD4Pi7vGEt93Dc0KS"
     "Y5wF6fklMcNt9x5euxMzlzUQ6sNgZbFzZbq/Be56d78YmBCZHlOSn5CfGTO349qVxze5KaQs9CrAdxSpsApM5Ycz"
     "+RPceWLFGxTNB5/nT+ISJzGMB7EU7FDwUPZ9hZjgQvDHmcDTQxJgJyKlVdOrG9tbmiY6wGvQvhDwfIItniyoUuHq"
     "eKAJ96JFimS6gM3rf6fNXb+TOn3pb/vloFhej9xBaon4urVgFffSBPvwwELQDl4D929HeXElBPfU2+I83RFxPreU"
     "RJqJDyjWn/Mr2SMwv//oK+QUCKnpEdkXty9O/3J+GlWUFWSbyuFMtQWJsqjz09K+3L44+2JEOlVYwAHFVHa9XT1a"
     "Hawe1e9fUG7eGxhPdY3mBomeX3c17/N3Gr7xd3r6UAa5WcTlomKBHkcZ8NXPZwjrOUT/U18A7gwiqQXvWxh90qdw"
     "N99w5bmIxY0RUuID9btnlETvUwyXSBTD0aUcdGe+trf+L/UUaUC2Fr+ASJzKTds6UZA1mb8czLxLCM+0zcweTZ0b"
     "Vb7YMU4Xbmc3ef5xo3ZTiL5Ly+0hkurwc0M6HG13Zn0QpbKPCBmbHYujnRnzc8eTBmRZBII8O2nIsSxzUUzlh7hs"
     "ZgiOstsK0t6EDf7x5lmN3HlEYgPXNxluEiWfFhewtwvp444lMdWZix0rkmfLc8GhjaQh++bU/dZNK0yJGzXlLsI6"
     "TjFP3vyBb97rlaHZ6p0xJqI8C++Tpf7MM+szju6bFjm/kDPF1aXckrZjS0bKzmORnasEuCYM42EY0H/e7JKuafrz"
     "5U/1fweQaJwuhZjnPl+k8VNh/Zype12neaKdfirl8FhnyqEutawZB6HuXTcnX8+fTQ0gsMEdjyWHF+d8O2sw//2J"
     "pWML2zM6iLS1MtcPGBYJmiMbkHtIPR5XiWGQ6KrCmOSt72bLAk2qcsm7T29q/bDc8v709KZWsMajaqO2cKg1Lalm"
     "SswiN11oLjEUFYbUJfsEhGe4V49H0ljynvrLyerpVNruSqvpbpIzf1lQokJPJCkt0pHw7C/e3A4+KSRxDL/ak7h5"
     "DT6PYhvE5ygElWUG1JlnBl8dELpwggrzfRI9LFR+U2rES1lZ74u4gvQsEsVkTdxhvCFLEa4PTxVI88tysqsSvNJE"
     "B2Z68uoWeoj8PeQpMmBBPvTXfvhy2eKBsjzlNyS6OtAVxVRqXD0RaUFetnUh75BOCr45UoX9BiHuDYFPIR5RthSP"
     "TBxZlvmRFZVe3p2MhZSkxUbCCv/XMVMY/5QFgl1qniA1MlpooZLcLlMm3DQTX0+reDYy1vTx7qJV2jmeYPI0k8R3"
     "1edGNgXy+GXiIkeHIyu92hHwCnzjsWTfaMYPfXMcb08OL1/Q5lAuJVI4BNy/EP6KqSLxzRSkE3nX1Ya8RFqIuHq1"
     "CiN6NxQxiVuV5+dFzGOlVbVnYGWBDxlTY944xVCTHistAWbPVe+7hl6sm9f07sbwiPzfmSoqlUh68a+dRPvoy2F4"
     "da/azuT3tNJoH1iUrYaS2L4Xh55fYghP0ymM7xsY6PwXDO50R6cLqXL52kOLnm8c/xdZXIgWdjXlF7Y0FRa11hcU"
     "dNYBlecnKvL78oa392av+eLCE+/DeLKPx++7NlLw/O9rYKymXEx2ZaJYUuS8RBrj6haz4pYcr43nT5f+9kVjaFJM"
     "A7iPYWvw2tXsEv8yvzDgCPMv8w/kyNoMp1e0z/BPJEq4qTziCVbSB4GORWVTA4roOm8pJ3Rwb0AYyAuDMImNrsZp"
     "12AY8JvddjMxPa1qN43ec39eD51JeVUWkcbVRnSK01L0BCYb2dyoSpt9fKj8wfQizcHG8XW51fZ5ygrxEIFRp/Xd"
     "h2Ea0KJZTdKuqS7YuqLreJxtX3hGaNenLY5AmcoaE1AgT86dCeZBTI2rJ80s+vf0w8374d3IpMd+i4bisjPG9AXT"
     "85qRZ0gzEVe3DcJ+kTzmwovqWJtZ0kTvkMFKHN+FJ5YD9qsF6dVtKYmtTbbk+o4ke3Pjb18/gPAhhPeRfQ8w7AmG"
     "bcQlgLpTVfpJhxP/KgHczBVppR12a32LNamqy2arbyYZN42VfzffOM7g4j5euG49oM2Z4cJ8Mee5uBrocW5uIAHC"
     "XyH8EXcdzMdUavwA1ce9QzqMLZrC+VohliH9IB7M5szl0PFpPcEXxvxnZle6MXjXhCQ3j4HhkzWpHSSCIsXWmtQZ"
     "5VhYc4gh/JJNF/Kuju05ltl730TG6dC3L95uclEhnf5iBSDxlwmftBOXu/Mu78pGB2LLcWHLzuJnASH+suRQ4Ipb"
     "ZOJOrjZjUXZt+YIEaT63jkT6NcVUj+ln7Fo60Iw8wzXxCZumAvQhXBcN8ukgHdmcrvJIiIu0maX1nNZQKzJiw7CP"
     "EJuFILNUyVFqqzm0jtsSIgNFTJrG3TXX4xeo0hBbKMT374KRDDJeKaA6eU5M9tBIc/0irfOSijPmJqRPz550tUfW"
     "lHLRasJu/KpwsfwTxDBcJR6pR+41aHCtQjwE2NNlPa+fDa5Yfmuw6buRZY0/3B1Y/RrPz/8zxL04Rg8jY3TCkvBQ"
     "1/wTKvV7j0IQWeHNyD/P4EoxGtloTNMcqJvo/PZJ38qk2T4GvzQ8nVUsYCRNMriaABpBpbbLNhVPzPzh+1kTsS2u"
     "XQoCHfb/FIzGyWC8c4as2z3LPiOcrjbUzVEbfhbn2rpShHHAjnrWHoK52gwiyRgP50dmPf2V9nBxzadry1ZmD2p/"
     "zyIRKsZbD3313WPJSTxFHBmy5RaFWJld66sS//O69CaZFT6lRFuiXM/0yA7oEta5/Cu3CkbDLPzztiBlprFRG/Y3"
     "oyA8xzNZHZGS2WbNaqzL4mYA694X70msDzFV3r8pD5PI/gRclhL+DVUZlM1IGiW/AOIq2XjlDe/KQ3Rix/N+Zdqa"
     "L+eU/BiYmNvRnFvU01agLJGQPl2tlQDr9TvvSf+9JrhhRTTiKIESTVKAUsSd7Oaa6/EPLwFny8vvRX5Guqn4Vu1a"
     "uqbpGoeO1/kmeCx2TWzf6HAuCz8V6eOYXleY0Tg9W10r0v6+qzwIPPJYemR+9rez51Z9/HrpmKFDGqFcSqTHenFZ"
     "GKYBTZosShaSSt6QpoL/hOvcyR4uoF1LlFEI7Yrf5oiURmVJyA7GlJjbeYHy3JaOnJyGTsCHl/1navHRZPKvflt7"
     "w0zcGzx3OmoROHhJcdslrAMse2FV8HAcE8I/IbaWELM2CrRpMQwkepsWS1P+47A4OoEhPtmFI3QoMK9OP9GExWtq"
     "kjRjxOF0zFgWXShr4mz8xoP85ZuQODJPgHp6LvPzyUiW2gJ1m0SNEVWOFWuygUv5M/+27j1nKxotwz69Zmt7lsFz"
     "6EA1kdiVkux3vjaTMxk9d2p6rVsxJylYpKBWyHF8EoniFvwOn+qJ6skJza4EHBl5zv/tnUjYc9TH/yUpweMFOPsC"
     "wr8gNkIMGEHBPuAbCVoifcE+AHD/j9n4XUgWXvkrhmUju7JRdADDMFCJQTjARpfhZMsxrMd9OV62jC3Bpfk9rn8a"
     "PhWYA7dKr+x0obco63bNmZ41Hl/QV9CEf9QUAY4CYv0thIM4KjJA2R2hS9fLajgdMBDCN/sevxq8t1yuP4D0zIlt"
     "WMZEoCV9WGK1DtCEK9i+vv8Pf7UqA51p3GYSqQWP+dbzk2Y0NCv4JPZ8oUuFxd9iHwmwJk+sxlImgKr8svc//sa4"
     "Rf5G7hQScSre24At8tW/973LtQvRfmlV3hVpVVhj/hNZg93JRlvr9FOm/K2fwq0lEnu5/3nGfwjJyzgc5sjvYLM7"
     "7cr20teKjuDirFNBJf2o0M697/PGTx83V2zg1pGIU/AWsSUk19uAp/3jQv6JAA5SCcp0e3fq1OiilWhREXzFhu6k"
     "N6qiN3VkYjV3XnDe/L+8nqJfCehbHFMjcsxtxuYwO4EQZjM2WlrU2VMdW+jCIyj0/MP8i/0NkeRhdLdHnvF7sJ/5"
     "sDCv5nNVrgpBgEsdp0BAD3CoO9XtAZlUHDdysJV+n3IqYvpuqS+ZLfqwGQy5J8BFXkZuI4m0EO+boB32Mi0N2/yf"
     "zwWuXUhNC0w8sarHftw3JX4Nwr/zmQXvfUHBVMpZ4iMINZNPOTeK6wa1WRtkebpppqHojoBEPPkskagQS5ojMPiJ"
     "vVJAG7BOlzv0U82DMe0SOwj7Zb3r8ng7YOHdTJ6ljFwcp3G3rnKkp75mbGdSRUa9v0mSjmMvP8TdhKlmUJCZEM7a"
     "F5zJkMhAfvjjMkawpiIxxlAbA3D+Tx3J02emrJTYq84nzBjpzE3q60uZkNirL+lnjrA64gtTYvXV2SZzTWysKdcK"
     "SH9BVQnlFFJM+BI38tU2DHsC4SBCBgNidkp4mCKN10Fo9gmF8CmGqUCteh0pbh0Gb4pT+hjEFdwuq8aAvmCW4s+W"
     "QQhmEGSeUun1Rs5/c+7rBbLoQKmcUw6bh9NnTBnOaWxdmt+XYc7p9AHIr7MwbALDGpB7DZP4pC0YhmDYEVzzYa7s"
     "wvMAGzIKLjIjBEzb3IXz5gyN1qxyTQvZ5RJltkdjmdIYcXcj12U4Z9Sce7qKTme9ESR0+82OndV74kr1VF7vrZr+"
     "kzOTopbap0UlE8k4Qo1C7Mqm4BCznwoDEDvIPipkhKboavRVoVYK5VavrPNw/8C0E9ecfZHzPGdiByr3uFDsAV/G"
     "tX0/LZ/DaX4mF3z5wM0jLRm1EnlsBYdMwQebop0xlcEWIuUG8TWEGFKFYRiognCcjR5jrxDSBqy2ueMc69zw7Lzd"
     "8szX3q4Q60F+7t3HRnPlYtfM4MDnF6/xkFEM/vjtgVTwK0O/wntJZGQcl2IPYEoZB6acnxqH0l/9bOHqQQKN7unh"
     "kkA1cIOT0IZZPKrbbd5yoFiOwUyIxSHT4yA0omwake3VfDVtaNO0aQOnbtWDBMbkx3kzf9+4aSH/9Z35xs0M/q9r"
     "LlTfpXOVr0ar4A+ieDKBRHMZ2ac7fv/KqbEFX/zgVG53nzQTOAI79YOPx0Ezgcu24uM5EhITRPAOHkPWpO2dXabb"
     "W/DnWTfzi2tiMdfuyuq37p0oNe/lE+lsBYQ23LgNg8B1dUPJnIyocQqheopbSlR524ydMVmR00XNelOF3uSThXaR"
     "KOOpUYWDddMHz95u7EG77tYPnekplB4KDCZLpQlBknHXvzVmiUJmk6g1Kf4yqSUIPO7vOl/ctm/a+Mj1j43z6y+a"
     "Vw/mHWmdqHt78ND3i6dq79Dpf3fbshu8am4zeE03kwRtYksIuErAk90idWGN6QY1cSFnUbNQIsql64LDQ//MogHk"
     "Nz0GsyA2jPgM34LwKIRzAHMOd8/S63yPAkB91cJtakosCqcxV1GbI6Z4wJLVCYXzKg2wTe9QE8k6Qi+EQSApCMO0"
     "ELoBN5+n0+YVOHusmH9GbNCDv0EhalwSnOfFYwda+uojUM6CwkCtDsYk2GP0QStQIpdPngqtU8jkG8RlGPSh+WDw"
     "KXu7kBWaqS0LtVPJF7/96u5uQ52xpnZ8ZzII7zjPniJ0ybCUXD+3ofhmYE7q3qBcrSSv9q1PH6fO1SVd462PneWt"
     "1y+a5Ru/OCi3r3lOVJAjbzJI3nx+3nzYcauf3jbLX5+8aJVv0hJ5TvFeRc4UmWM71XMlul1AR472699vbL0hy+3Q"
     "yR9vxY/e+msDPJVaLhKBCgSpQW7UhoDMEAi3YNhRRhHTgT4WlejKDjHOwJtxNl5ZsTaUQWXM/6Myos1TufjwlhF9"
     "eGtM7isCpV+PsOS+xKQ0Neal5FCUbl5n+voK8rqsMl9HlDIZAxkXzq+pT9J1/cPGjhuK3PI990PPVzi2/+G5Dj0a"
     "ttiryFkpvz3znn6eKl4u8i5m4i5ewoATQrhTYMV1hMWCHroXTcqWVizBlyMY2I6BGgKfzvW5nn6ZRvIWej0uO81m"
     "ynxVcIXcl4UYYlGm1mfclblAZilfLLdg9qqV6sTf3OthjqAQb/YvDzOBvMHz6FdC+qQjUJc6K1Cf3L+amjQYWd55"
     "SVu2EjqO/uG5FT3S3UWmXf9705QbMLd6L5azEgtFnuyh3b+fEjM99N6/HKbI1FhvQ9l5f/s2tvTP4v3tQl5DJnuE"
     "2dxJlBvEWXIRI8ZbBXdz6oQsSYayTJJEJQ0okn1zWh1lBWOr0pOvWzuiul1obiE+zzPee4WEe7/vvz44sOljxbJ5"
     "vBRwV4cbSodkem1626bo1FfubdApLMOb8W0yMxC2jfpJIIlJ/fJPpuDTlL930LndqdOp1BkZc7lsuWn3JwFL7/GP"
     "C9PdEuI/QxnOE/LYNJd4jwR3luDTboWRwz86vMeFuiZ9gss6Qan5JGDqPB65MAI5ajGgdSr8zzHdy5+5Zil2uGYt"
     "eDPyQzLD1Zu3yu/mIV5LZ/ptyWvbL9V8AlLKlHpzsSQ0tEiiNysxnbnYPzy8yD/ODJT9LY6jE3MuWOvrziVOzMk9"
     "2jSx4tnfvcOL/5i67BkI/Veps5QEhoYWB+os85cxFfuFhxX5xZuQYKXB2kxeEqi3KlUGUwkNn2oG146unU93Prr6"
     "lq+/IeUPzy+2wi910LpIXjBNHZiU8NobBK5VmixlQdKwokCdVYmZTOX+YeGFfrHmKKg0WEpDg9CSQMNCOnOJX3jY"
     "faTeHI3k8dbiwNDQskBTRFWgD0upn8EMSCQPDLpA7Bp+zVUEQhyEVrDEeomwEPfro9BduYEFbHHi9OSs6KSERi+F"
     "vMkrOQHgKzy0yfH17uFYnbfFEhsRYyzwlSum+OXZcQmtufjdIAc5jDQfhhCBECWJUAyyIQjhVwpvuJHcaBbXURcr"
     "kYnOYoQZrH4rOB0TtaE/CK7v3INu8Rh+cyz2Iizch+EsrpFO0qNxLa14LntYeNbNg1Of1BC6iRmORftXMGrbC8Je"
     "w1AqoYVVUeI3n8tl9/EZ6Fb+UpqtPvSNIM/XZnKfT0kgcPcmkU/6sWg6hkE0VTrGCOOXlhI5e+3kU/4+DGdyrXSp"
     "IKd4HjPnFOmFVqWLsWzTmz0SFCB57cSKw/RmUvwDYALYJhHGE7RoJjLq0nM1hfFhMelK9Vk/w1kBwyw2B32/Gcek"
     "RCnm3z2w4szZKydbokdz63Oro+fW0rzYU74y52VZzE35BrOpVGfJzgI+hFGbNdNsSC40G6vzTLbqtEWXRBhH2Bo5"
     "kVGXmRtZpItINEco20SGcwL07ljSCXeXIMXiF/tWHb535GR16EJTVUq2qTC010GnsQFfzYCYCTcPSSAk88WKixDW"
     "E+/WYzAaqjBiNZeEawoUyS80294LIRCqGYRgFiB4IPZ6d2MQrDkaprFkhgQb0ot1uuTiBGlWUITl2jVOvtAlTTOE"
     "NS57vOvfR6L13AL87mODC5OIPsm89z4giKTgebsykq2/LHlt+nVhOtk193Lmef8+brgrvW38dZH4G332e3vTD/RC"
     "KciicpTJEOeWLcVgJgTBHZC0h6SSWHClgRfXT60ZIhE7Y4LSWV64qV4EpFRiVrOesQICQ0FBmApORz+iRdMD4uuq"
     "Hbj9DqNmyOhaPeQRCJID3ZflJLhFDCRkIlszG/QNAwGluwDEpKBcIwkAs2WkPaSIAAu+VAJKFFumVs8hkuJjdU5E"
     "x0CmeBKR0gBzBOsaSyIJLQrD4HTWaVZJnyS2vtaB7HcYI2YY3bo7XVZ7LK0yCCNmGbJwO7MbDA39AWX7AFSFIQWe"
     "5EBA+sTBYAzERIgeMD29lPKLbPYcwJhzGuk7jaJfeuS6QtAmwaARYqmEtSAZmcQlb1mEuCMLgAE3BO4z6qeRgA7o"
     "muvxFYrSkeeMbPYlmZ5BZwBEJ8oJSWXTABbg3BdtwSUjk0gyfi0oappML94Q19XxP4eUafDs7r84zGYc6M5fGlM2"
     "kVd+8GBeVflEzGR+920Ge8OF/gmDZyaZ876ne0N0WhG42rQ1tWh9TG/X/xxahjhT8u35TSjjdnX9ZHjFqryGw/sd"
     "BWVLQyfzqm99BB++ODBX35z9f/fb9ZfLB/2LQpD0EAhzTgMI0+pjMBcMBKvbqUAGhaMwqA6ETepcMCatL4XwHqbk"
     "Ewy7hwEww9y/ZX1HxfqUxNi4rhd0xsuh1jRDS19j8fQt+5nCNtaY0NdJXTJOICwfcatkC/yBxZ/V9iNgnttSmnJ+"
     "Y1HGLKFnKEo/vakkpZIvA4A1QChLscbFVZAJW0fdnUwyx+rHqgD9nYJ+1rDQx+k+upxAWLqE4vQVjrH6Bcxzy6Y1"
     "lvTNTDW0Dr2kM17MLsw4s6Ekddk5FhC0s/wRM14A+8atcaOs9lSlKac2FaWjINFfdBVlnN9YmrLsJhC2M/ZuOdlZ"
     "sntDtmF09i8Mxi9DMZZIe7xqVp0eblnPELawlrrqnJY9FwnkoZLkuBKdawAwB6CtYEabYCY6DJ6+4ticFtc8RCYN"
     "NaXG9KW5LUVnCJjrlq1sKVj4qtj27RCewfhl9p0Sy28LWwp2LN0Ldp/SanryyiLHqNz2gF+NXBa9t9/TqvVsfLaP"
     "+vP0kChVd26ZrXIyHpNeW+ZpC/Yq+vi6vHwfcEvAF01bmiI54MLNCPgFbqUXmonpHo3PD1E+cnrE+d2jSf4g5c5M"
     "HuuJSr3srowi5ADF908AE65qonsKKyhjVG5mwK8GH8zLFnmqg9SfZ4VEanryyt1AK07LZ/5dKzMTk72KP35egFeJ"
     "H6fo9A3VaVVtNN4r1cuNPFZx77CXOcqz76drFPQT8Pn8erRhalV5dpnLafx11kPE9o54mbRefR+vU+Xrwe/rY3S9"
     "zpKqNhfub0xGw8nv83eXj0UbWvzxissLQFssVBhEzGA8ec+T7pjK72ay8uCeuiUZwau8J38JihOLXUX+IpSF0jah"
     "hIw8f7vC3SXIGJawwPS1CzqTRWM7wZdOlIa6MyhHVNNDE9J2Mzmx++O9XEbgrHMMEhcOTyxHglu1kcH1QLf/JXqX"
     "QfTv9kyXKzzTlquIDAqX9lVl3r+ooIZBRKuDOtSlPBFKpJuF7LfOnIc0bgiDoJrjlamQeSTlmAmMv9m0r2ocdIYw"
     "gEZERysEsZoKoRIlMtQC1r/V+V+NflIbk50hclgRYkjVRBrsFYFKpTPYkAx+WiyUQxEbz2bc+OXbX05PjxbOPslw"
     "8U8KSq2vl6AMW2hGmDsddYA9udSBqMrQckvOMVw3bVrtk7bIx2u/x9MTXP1dFQYxF89lvPj55asTPdF3fblUn2S/"
     "1IICPhu1BqUGeTDYWWBrFqlUsTR2/M6m2e3v+iIZ7wNwwboAAqENxM/SlXmbgyUhutq9Yf9q9FAdkwVwfv9I1m9G"
     "4g+6WgmWCeTwZwWHtVZVMp8U4p7Yp02ScdmG8PJwnX1mSUoEkXyO2AyhCOhFEB5nS2mMSM4xCIcgbCWepRAiHBP7"
     "GvJit5xicOOLImvcDQEkLvPPi/os1mek/7dWrvR3td5O5Vw8Kxn0xX8U8BJZFBaFE/9SKRYBHfBqDwgANgmK7oLw"
     "NoS7UFQFOvBCAp3znXiqN5/5bASBCBsY/RpbN/WsxFQaXKuQECAmLiFKnuJ1HnUo6nND+tSXtQGgCbh5wIi01O84"
     "WNzUdKpUUZVI5ct+fPGn043GmX5KVhDZDIo++NB9IOwjviSTYhuckx3HG/ak9J1zHKILv0QJHr+n9Sz+P/l9HYVc"
     "F+enk6kL6o9G5v3hibCPCOmHas+l9jXt6TpeORlfTyLfJG6HsBeDp1GUFcY9g0FGtDcGz7BREg8Tf41h7ET+GMS8"
     "oxkQG0NRVgxvKQSNK46BLjnJZh+BcCOER9jopBJHrZowbCA4IGQSj49GstEtc87KeimReq+YUvEwGAYB/6YP62/N"
     "Sgol99M9Fj20KteSafmJzUwCJiqlJ72Z5bKkqjc1e26llMb6PaCLQs6+eZFF8+jsTknLy1nrwpqe2kWlbCtfh7os"
     "ya5Ly+nt8gDsm6ORlqq4WFuVRpPojImxlV9oDAEZIRCCFwMxDHPOX4i01rheNdLmjI22lwOCQQvhWwwrKnn7ZcSt"
     "A9sh9h6DYDsGf4YgzqJCmqCANceoSo3fTyRsSIk3queI+HfQxQLmmqVW5aI6C2aPWNGUqF3qx2T4LTOpR2osKrtm"
     "RWuyeukapmAG+OmJQBRaly6tIBM3pMYbVcuZQiXShKHNQsaayWT1iha7xoKNVJvUy7gMJnepST1cY8bsmonWJPWW"
     "1QxhHwq43CfgCIRzIXYERfswbELU70PRg2SOfLCKA4smf05n0zMCwA6IMTEIdmCQA4Eh82iOZWwwryCtR1mqz1aG"
     "yxZVJzb61vn+5FGWsXwst9zYoi41Z6kD1R5JWvdezw7/b4DuuArUYBCehbAGd6PwSM8hXMRmr8PAYNe00e64Mw11"
     "+t3DNR09400Jh+NrPTLSojGEMV2FjB97w+ILZ4TH5888SMifZSide9ZY+jo650+i+zYckypg/lDjxsLiC0x5M/+Y"
     "PmcseROd/SfBNfLMUneSw9ccEOhpxjnc3XE5ngmBoT46kB3d3jBldXPisdb6xM9X1HdMX9Abcba+JnLPnJq7yz1I"
     "Dh9zYJCHGXF4uOOzPY2SUO94JAscFjwLPbs05daGNN+tj/HT9t4IP7Ah6nKS/8aU+TOzC1LKo6LIpL78uBhjQVrE"
     "NNfZKp1woba3JjFN+Zm3i0vUAs4oxMqI58rcfhT7/+iWSc1wX1D56IsZowPHKzp2Rjzo+PRXwP/ZeqhN0vYtlend"
     "u3Mam36qc83K6E2eORpJWLzCB4cy6N7+ESZJiJ+J7PD2phT724Hhp5OEMGNCmcWpSZrSc58p+BN96srPmVtBIufY"
     "0g7Zm2Y/axr6ZuHkoV+X6D8nEyKCjMZ16c3ODZ/l1rU8KDPm72Iy16TJExbXiJisreMJQSGKGJ0iKKwsdZnavvQL"
     "TeYXnLkEUgE+3Kc07LloPS/MleqVHdoTPi2gIgPBhZojUhvXR6SmUWpnp5b0NRTElyjBjhXP0Y/71Fub/ObuJ3SQ"
     "KytXbskpa4QqPWEQ0SHzcMIF7cj3SBsJ16DB4EFPa5A3hwX6QcOjhrW42LVslPGC1wN+7r2AzL0A4WGIrUCU4O7C"
     "sofx5gTApjdsnrvp0sw7tf4sjjnSqY2N1VuiZV9liGy57uOFjsXOzIghPVxGJlar46X9WScvvb1YfNwab3qGUsXW"
     "QFt9nRDljqQroqEtRAut2rbgWbK2FOtgXZZ2LD5CnEUkdc0NmZE2tfza0WlkQz6s1kVJ5iT5iEKSFLKI1Gyw48C6"
     "PxbteJvjs4Q9nine+v6vRZMb/1iw9U2Wz6jHklzv7W//WLz2n/atdfV7VFfKndjFhg1bylqbtxW3rNOcc/JLNV+1"
     "7NhS4/uEXVtf+/tBKn3dzhVJtsy+5MyZ0uW2hoRvJvqnKWeI9I9ZVC+rb2K+7ROT+84/5BXHJhZxEr8NFv+dBzK4"
     "r2fWfL1v4TNrd9v3iWcWdXzV1996+eSiH61d015Ydi9wXm7EtZ7Ib93RNa1t2+nsjsbrjqFtvY6UhQPl62DaL1kQ"
     "3isYSqwOD7c7Bii07//hCes4JX6nw7u0NFTUxJZkQViL3Pg+yQP6aONCXSI8AO7bZypYosRxiTw/xUs5BxeCYXUK"
     "DgHUEQh0HjeDCQGemPYAwgpwqYLVJWCesVnMVh2ZnGa12i3PmfxWJgVXjlzEl7MVTRKJJ4FPpr1N4vP7WHQyj+AZ"
     "GgwImQd1xsL62F4vtbrbuzZGXxQfpyusie30UVHUPV51sYaiCoEkPzBclucncb12y9v71hlASdh9OuBsh3ANhxbh"
     "FiKFuBO3Rk4sxp8A2UELF3WMAqTfugkt90accSOERAgzC4Psm5tIlk02mgwh/D8Mg3wIgs+TeVl8lEFM4LezZgtY"
     "iydiddMH4uK7PFxoIVXxcdMGY/UTi1mCZUxANE41OIv1uqpivaGmQKcvz7+nN9YW6XVlJbr4muI4Q0UuEPLI/EeX"
     "Dk48RwV3mJe93+QftJTRhFPYQNzhT23xYKEdW6c25c9/w85F7wvph2ouawvefOcBJOfJbkbtaxapKMP5iL+E8Z0A"
     "/Wki0bh8XpKu4w8XF4ozWT8x127c9hMq+I4J8Lf2JdrKuxVGY5fcVpbYvKarOqELs1Xu0EstIQFhdwMDycFBpmCg"
     "IXyXENFTbU+MLQiyqeKD/AKGZmX7fvRG5cq2uRu7YU6oPUoX6u1nM2vF3mV8QF7CmXq8x84QGv2U/Mf/O+83hwQ+"
     "j4XiMT2d677o0sG9jNOAWEZ1+eYBlYyTV9UHW1MMlsT8Dqyfp4nt9/VPBsj+bgj7IJSBYhmE0yEExICNxqpig76q"
     "0GioLdTpqvKfxJjrShPiKvJ1hpoyQ3xVNhD6X+G98yzL85rAoYJPjKveb+p9/K2raMI6DnAj/kNt8WCyB7faok1q"
     "2czYBxwHel9IC1ckSuMXkNyB5DxuFPaQsGxesmEeQ87veu+6R26sWdPcarU7e1QGY5faVrVTF5wYGBwXLA0KDpEC"
     "6cUzxopgu1oX7Be4daDaX5ieIeoZ2TBVlReaFKUP9Q6eiI/MWScP4slDE6L7G7JKhUK02Z+6t5bFDjqkD+vPN0i/"
     "QJtQioBJ6wk35yf+7AoMS9DpO7uTGHyDn4J3+YO799fLBN67hBxVip7GFc744uBe+rG8jF8/rNB4uaUmyGSPt1iK"
     "2lSz+JGx03x5scCnAufpOhtlmQ97NbFyBKzCuVp9x1B0fFconSationvGYwyzG1iCqpYwH2gOyqxLj5og6/N309k"
     "OxMYYy99VhpvqtVqbKVRMYmVGo2tCnjcIqM/vukpeHT4LsqyracgHt91H7zM+J04wgYEQhUGUYh5Ur0gZELoRQU4"
     "7EhWbdnyYJNpZUhDeXZMfE6lqs1NmbAirK7yhl2eHBAUnBmkgBk+wVK7GIQHoOG8RpkzJV4bmaGM15V5uA42I/Sp"
     "PgphlClkRUV9VniSWmeudHW1GtnpjY6IP+WFADcSAmjlbiqLJFS657sUL932dfhKd3wXTul+bM9E/sDVclZw4Q9j"
     "I0Dps1q6dem+RpheG8Rv4QVM1pMoMFmRj8BkPaGKCOgWV0SBpaSLAkuJEAWWki74kAemUqaJhnnCqiCi0r3wjT+k"
     "20F0T77jMXjxB0EtvZqMTc0ATTYswl2QCcdBJtwVI4akpLEqaBdcjXHlaIfXfNnhZds6vOJah9dDHn/DAdUwxtnN"
     "fdfMfphdJZgHzDDhllhlg0P8FbOF1LFX+9swpO5SUtkOLxd5/JWSozosu7FhWr5/1UOYkL/JtSWY4/LoDlxZbb4x"
     "TatlITkhm3jNfJ9dZbdD/BUjWit5bLSQEN1jeGmZ/OeOfLw752P36CxvG4hkHgW02HatSTgBVZAG9051m+mhEF7O"
     "ht0dRu+ZUY/TqunXzcBCiHCKtA9ML3zGXWFMt4w715jeIM+g+IKrNe+tGbgdrPvTHLtIGMLBB6hsodKxzFZ9IAQw"
     "+dpDIED153pS76sunNkAr9Y0Kxs+pZxP8ZDxQ+r1nJf15cyD+K/m+wlPZhBy1wDpyjTucvAb8/UONH86NXtgYLyD"
     "Uc45q3HTRLWvmtziKEDTmg4AOylfzij7DbwaMMtkDn3GCP6TDKp1bXO5BDQ8GDGimBX9j+L+AiK89s/fDU5S9+zc"
     "vv8HHiKlm/jmBQWXiWTfG/BHgtbrXcb/L9EuHjlazRUAW2ehwPppz1tB46W1/2EK6s8BbX29u3tQK+k76+xhmU/a"
     "skx7YNoVdO7Fdue+/TB6bV2i9Sx8Tp5fNUMfHRyr20ue3InQivg7HzetlUrXkSKmSSlcKVLM7Rfd7/fv/gMS9Kvl"
     "XKrX1MbzpVsflF2ZFI36MHU7cKnypsAeRuq5shMqh1hj2uV0IPWBjOTeV32p/ZSef+TOqDmmi6KoUpx1tH2dPfZT"
     "+jh10WnzPkXn0RRJVG+XH4Rt4byHSVY/QjtZKJyiTpLUH8S1/ZWf0b01LlQ5yqf9wPpWbNcKbxdx3SKsblLVe249"
     "KDzFfEoqrjzoctkevCI+5xmfmy2rKkTm5L7MOKm9E4z/SEu5XVruFZQxFJilns+E0ayUKuGGW/MokcR4SBv/7a85"
     "iZafm9KS5eARZVLP5SVTfOms895Af7SmKi3sxbAXr8hNFLysbPTUnZsyQiStVipndoSo5JlgX7ChXsJauE/qWwGz"
     "XXh9qalKVNUXZpdJTj2kK5XYUpHJeOROJ67P6E8D1fThz1LxfYCy7tJNLhbyJqj/EV6ZEnKavjSqbalvYkJm4BWG"
     "wJ44zRIuYmKpgjChxH4ePiE9UUhAPXXVk9IfxaBGGkvjtYYk9evvvfy+Jc1WIWtEWHbVhF+rtUp4SNUGiN6+w1oj"
     "JE63xmHa1xovWueqBNfWRO4KZFIb1DKzMAvYof3m2qyNlsy7pS7XqkYzsTbhiKRGPfymza/y3TGFiZ2eE/1SjZqs"
     "31DaHyaDU/0aV6kpqZBdVq3WxmgjX0rh5LExZH8UsxT4ZtwL7KX0tEoH4b5bqdfsqw0aFKLHJl017BAFOT4s+JkN"
     "4dwMZ5KqdfNrPbqcnuh0PHX1mPHbyrODxqVfFeC4v0OZ8OmkSUMzrdA0jktOv5T6rcJUjiGM8SeRKRORD5NgoQi7"
     "fGjf8aHbxvT+Tk4VGpooia/kj9ANw5aK2XihxqFrpobO8JW0EW8xTuRG///VrdLsHzHcly4ps0u5zywRQKJCoB8F"
     "cfrCV74WLIRUqG9cdsVV3ZDvLqdQSema66rcNGy3PaB3iiJba9xyW7U7Imk1OUpvUqMatY3RWo0arJMwhMNmr1k0"
     "j33dotbxzonsgdOuU5cODZKfkipNt3Q9ppiq13rT7JXhvUx9Ej23+lumm2GmPg558hV466hCq62xTA1FKolod1WU"
     "/01+8rNfHPer33zCEOec2byw7ECwEQmb2AZELrxx6BUpESseDd1++6CBj8pJp1xwwOcOOuQ8fLQw4ARytDRoKaYP"
     "PjrMl4iPUaU2ofBDNceQ+eZZoF+xEz/QxQ0doTNY8BCFOCQhDVmEoiM6Q4S00BP3LGLwwGP3YyEBpaaiqb3e2dbG"
     "qOqoqa93NjiL51S2M0mTJyU3lin4KILy1PPpFTXOn9GX/1mf09TfVKqdyAWl5R3t08xf8uH+YyJoKopKEjle0F5T"
     "X9GllTsrSsfXlw6z2tpbm+qcHwgCPsXOBz8fNGD64nTKkaHA9cpZipE3o5rpn5shWgi2ivDf0gweRv4fXCUsBA=="
     ),
    # latin-ext, weight 600 — 2,760 bytes of woff2
    ("600",
     "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF",
     "d09GMgABAAAAAArIAAwAAAAAEhwAAAp4AAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAABmAAgUARCAqXDJJ9C0QAATYC"
     "JAOBBAQgBYRkB4FqDAcb9w5RlG9WBeKLA9uYdtBFmAgTbbQZCKNFjjeDxb99i70gojyqepBkyZPor8AMz+b6t2rG"
     "jOqHFcCi8cReJGIzI2J696My59V9S8GTU/UJEZluA7qka7Px+sXO1IEI5gkIyZ+AXALz7tfqhmpTS3ChYalRym5n"
     "7A+zMcyGqFaxROi8zqepJtfQCIkQI49oj5W7OcgDQcD2K9sFRn9WDYEI7GKbByDpjs/WKxmoUIAK9ZSySmkH0MAl"
     "VqhBmUAbIGVKCfNfMx51G/IuTgmAABjsYiAlAFDCpdEIkMZWyFaWloyRGtbj41zAaSnNC/Dmeau8k9QFdUnd06K1"
     "9lKm/N+Hwf2UlOL5jVeMQbv8R3/Fb/RLAeB/AfOv/mBb6l9MwOAHXxAoTSQFUIeEnCEIhxACCRPyFN8njKbaYenm"
     "yQB6I5i9NWweVdLZOOWDRgwHwxXBDohH7b0hm8OYfG5jgaZq0QBSclMqUu3s3LxDwuqt+4SFhnh6OiHZ+fUbR9kB"
     "qVOSYvEUX65O/g2IuLNPl5fQmYAJaKf2+QzxBP0Z2E3DbsYRL8149A54E3F+hVKZCIFIr7uOMYDT7mkgjOxJcCuh"
     "CnRSJUU0NlDtkPe5opeU+e1pUT5LCtNCICzjFtoSrRkHMJezAjCDVIApynjNlKy88LRYEGGICEnhoKQqKQ/Ndp96"
     "mId8rvDPV/RmSZlG9qTX28T8GbusMyFi8RTiqkX4WvqRPZkEjG7046URmuR2HUM7VZLHBA3YmWeyeuNZnQV24yIV"
     "LUrmaiHmZh+Fn8s5k8lXSIN6mcwj0gtEqsxsTOBTDaDGRTAxxSxd6QCqOb6v8ga9K/a+hn6wz494RI/7bWZ3Ai0t"
     "bloPVPegugPwO8aiFzMhj75U9OljGyIdPYnXKHCAdRkMcaSD4fEGAfGyknLOn6uIDNW8jDYva5pAGoBolJqLzc9j"
     "9Oclw6uGNmd2T0eKHc95Extz0khyiJBSHtqO7EXnalZvUyrYc2gHvqiNRFJAaO65oQ/R5rLqcUU/JCnbKUR5P5pW"
     "kcnkJLDgdkDrNAg9kB8WiRYkE/YOkQ8f2KVNHjdKL2kdNfUenF/RL933aTKmCSNAYY2BloE0TdWPJ9Si1ma4fXhs"
     "27PWaDSX00sdC2Fj8boQnv0diq/xHqoHJ24RYEsafgDVMBgQ6XR/SJUNAhvQPLZ8vNyHhdUl71YRWV/3wKhHvwv0"
     "gW11XP4CzTOaMB/jYjzOgu5vknzHc6DlfkZdtbbHwN5LCfwmtUT9BmedNnvfmXgiMzZZ13/fTcO67zede1jcdrZZ"
     "Ji84IgQRsnseGBsa+cM2BxXxU7RkTEWkILFXZpVvB1QAAjk25ViVs1xrrbovv1yIJcv24ohEAtsDqcecEmNLdaQm"
     "oDWUPYGOpWTpRXj0zQonPOJuyI+XybpqLAFiI8JXOkcolZ0VSKm6+5slCetHrtXMsMlmYDAWwru1oKydRXxFWMW3"
     "o1rfiI5/NbGsp8jZzLg7XP7mE6fe+HLC86OasVnTVZp62t5y/O9YHyIpuxka6jua/S6Dq7M5OvPC0bcPrpS4C3me"
     "A2uc8VUvbb/ZcslZ5W0X14Xk8V1QX0xF5Ht3042pdN0VabQuIBaP1inq1VyX0nUdij/TmDPWgy4lyEPmI1dfXoe6"
     "5u5Cs+fE8TkMi8EwQOyLyDvquD+ffOr6J905ReSAyqyYJGGOMmZXY1vocoYu8l7h1fupO07pT93OA+pZCuVf8jzq"
     "ImL3ZOmMlvQ1iwk/x3upY3Py/BUZb1z46LzJN2PyYr/lSRvhvd4lQqWrEaN7M5z3XHKjuFdzlsq9GMN+z5PKV0Zg"
     "S248vpj6L9IRLRVHtjnlaFxfJZY6m515pjl12VFMn9TH9K2fXtRTzqEXP+MrefJNTKskJhZJSTk9O512Flvz8Usy"
     "x2vZvrPOqw/cQ6UP2bt5YB0YL4BhD0ccxsunLGPl/fiKcbdpJtcmkAzFNlfqvEj3rcHfIixxiu1KqxV9xLJpp3k6"
     "zw6QqDuygT71Pcd/s6N2BtscedPT1KLgmMy3b8SuR46fQ5A38mKVIJQbwjciEC+4uwV4ZswP2/8hO5sjR41wVKy8"
     "Xmd9ly+F2gx4wB3NdD98+5RuJw/0IEBa55k07CSttlWwmiqALpa3DPRn1wgIDzsuL1YM6CwQHo8g9/EH34dBBcx7"
     "LRDkZAiPBRCVXSYZH4GzwVmSQ26cCLneKCk77CXwoB9vG/K1kuFeEB8tib17YWrRI6e410KvJf+6yf6H+j9wiBZk"
     "9cuRTSRrkH5XLHOuw6+de5E345S3d3o2x/31f1+gebYw0dDwVWjI4L8S3qq/xzqhV9rJMw6qEYxUHvizX3Xi7INq"
     "5JlZSBwuVlHQfFauwMKg3dbiLrBWtxVk5+5u1s/4IblTRdVU9OKBsKfE3oiXpGVbTQ1ZacFYIEq3Rs/6SIL16Mlh"
     "D46zrvfyTSMBQ2vYhZNDQbKN7QaJ9p+AXslq7bgrKjcZa8o3Wt6K7EPejFOU5bIVtx0VJ5J3ViWUbfgqzGlOM++4"
     "n6B6Hov8uKiK4fSD6vjMH4GBXjsnceZBVf2VP4Z7fBZKZL8TkvQNb4XLaNXH4SeoS4qdCho1jr4kwvLNTK69Qx1a"
     "8XM/TsPGacajDfjMTlMb26RQJh3QjC9uNePR48NiJ2iIqpej6YlT+6IrR1xnf+BZo7PHy0bSLfe5vgt6Vod1iPTH"
     "RY/Vcl99vag9TjaaYX3+5rsgIDQdMIhALEWWmgeqYZ5UGVDp4QEuiSrIcxDck/CZKqkvck/qH5HV+hL3BG7ji77M"
     "PSkDcjVUCoc4Y6wj1WhZ16KqSwHUzwCw7SWWy5d4L8r/pGPdKnhgvruFkfu/TRa3kSz/kc5m3yM9QM+zpxFAwdwj"
     "tfN8mqZvXqIHAB58/2MAHu6Yudsf+996UasCAAcFXODTaSrwGjOY/HsyAzygYyoDaGePkWFWMH6QpNsB7sk3PxG7"
     "2kCuoJYRr94kl0dqfR/pHRSAI+nW/581qdiRRdQVAc0kjhvkJMnlNJqSRW2JJ45EKtaigvqNoi1ME13S1A8iFefg"
     "0h2hmVSR1vJojwAxASDxfIZ6C+l5wFsRym5vTVFmhxo2b0sibm+H9NSQUEQAOjJ94z/CFA2Uo02EmGSISKZHUhaw"
     "IUZbwTEJy9KcwogdAiaiNMA43E7GUFEKDTOQIQbIsTDdJDq5E465ZgZVlFFx0xVRbMQEBYVpABKGHZxlph19Uizk"
     "DEJe8ggLzlHWbWwQNoVAhHQSAdOX5Ei7YG2OYRhCI8OZuURClHNv5gwKspGzDDGxGYKbCMExFsHDcNkLGRJoEcJL"
     "GcgcnNmzlhPMgK5M9QspIYO55GlGVtCpTBazMISHKCM7y8ApTsfcKs3CCsfKBxi6Iyithk2RtSXwgXD/z0DeSSoA"
     "aXmSCzwmP59QlLspxmc8oT6f0ozP0aJYz2jRYsSKI654EiCBEsQjHnBbgt3uwe+nc5XhIaZ8GN3LqzNcVlggyiBO"
     "gdDMtLYQ3/rjedNDo2HyMK0cLu0OVYvoKMN1v2unLT+4ro1Qh1mT3HgjCf/cQM07eP64nWYa"
     ),
)


def font_faces():
    """The ``@font-face`` block, ready to sit at the top of the stylesheet."""
    rules = [f"/* {LICENCE} */"]
    for weight, ranges, *chunks in FACES:
        rules.append(
            "@font-face {\n"
            f"  font-family: '{FAMILY}';\n"
            "  font-style: normal;\n"
            f"  font-weight: {weight};\n"
            "  font-display: block;\n"
            f"  src: url(data:font/woff2;base64,{''.join(chunks)}) "
            "format('woff2');\n"
            f"  unicode-range: {ranges};\n"
            "}"
        )
    return "\n".join(rules)


"""
Brand configuration — deliberately separate from the design system.

The design system in ``design.py`` owns the *language*: the scale, the rhythm,
the component vocabulary, the way a status is expressed. This module owns the
handful of values a brand is allowed to change: its name, its wordmark, its one
accent colour, and the line at the foot of the page.

The split is the point. A client cannot restyle a TrafficDom report — there is
no hook for it to do so, because the components take a ``Theme`` and a ``Theme``
has exactly these fields. The first client to receive one of these reports is
not the owner of how they look, and nothing in this package carries any client's
name, colours or typography — a test enforces that.

``TRAFFICDOM`` is the default and the only theme defined here. A future
white-label engagement would add one more instance, not a second stylesheet.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """The brand values a report may vary. Everything else is fixed.

    ``accent`` is used sparingly and on purpose: one accent, applied to the
    wordmark rule, the active status and the score indicator. A palette that
    accents everything accents nothing, and a client report that looks busy
    reads as less considered than one that does not.
    """

    name: str = "TrafficDom"
    #: The small line above the title. Says which system produced the document.
    wordmark: str = "TrafficDom Growth Engine"
    #: One accent, and the tint of it used for fills.
    accent: str = "#0f6f63"
    accent_soft: str = "#e8f2f0"
    accent_ink: str = "#0a4f46"
    #: The brand mark, as a ``data:`` URI. ``None`` renders the typographic
    #: wordmark instead — which is a complete design, not a placeholder, so a
    #: report is never broken by a missing asset.
    #:
    #: A URI rather than a path or a URL: a report must stay self-contained, and
    #: a logo fetched from a host at open time would tell that host who read the
    #: report and when. Produce one with ``python3 -m growth_engine.reporting
    #: .brandkit <file>``.
    logo: str = None
    logo_alt: str = "TrafficDom"
    #: The standing statement at the foot of every report.
    footer: str = (
        "Produced by the TrafficDom Growth Engine from verified, published "
        "evidence. This engine reads evidence; it does not collect data and "
        "does not change anything in the account."
    )

    def tokens(self):
        """The brand half of the CSS custom properties."""
        return {
            "--td-accent": self.accent,
            "--td-accent-soft": self.accent_soft,
            "--td-accent-ink": self.accent_ink,
        }


#: The brand, as exported. One mark for every TrafficDom report.
TRAFFICDOM = Theme()


"""
The TrafficDom reporting design system.

The visual language for every report this engine produces — Growth today, and
Analytics, Paid Ads, Email, Social, CRO, Retention, Commerce and Market as they
arrive. It is a system rather than a stylesheet: a set of tokens, and a fixed
vocabulary of components that consume them. A new report composes components; it
does not write markup or CSS of its own, and there is a test that says so.

**What the language is.** A strategy consultancy's weekly briefing, not a
developer's dashboard. Soft off-white ground, charcoal ink, one restrained
accent, hairline rules. A serif display face carries the headline and the
conclusion; a sans stack carries every interface element and every number.
Whitespace does the separating. Nothing is rounded like an app, nothing
gradients, and no surface is black.

**Scannable in ten seconds.** That is a layout requirement, and it is why the
conclusion is one card at the top with four sentences in it, why the metrics are
a single hairline band, and why priorities are numbered rows rather than a stack
of paragraphs. Anything a reader would have to *study* belongs in the technical
drawer at the bottom — present, complete, and out of the reading path.

**Why tokens.** Every colour, size and rhythm value is a custom property. A
component references a token; nothing references a literal. That is what makes
"the same design language" a checkable claim across nine future reports rather
than an intention.

**Components.** The full vocabulary, in the order a report uses them:

    page                    the document shell
    report_header           masthead: wordmark, title, period, key facts
    conclusion_card         the week in four sentences
    metric_band / metric    the headline figures, one hairline row
    section                 eyebrow, title, optional lede
    channel_card / grid     per-channel health: state, one observation, figures
    priority_row            a ranked opportunity — the scannable unit
    idea_card               an exploratory idea, visibly not a finding
    action_group            focus now / continue / wait
    insight_card            one short learning
    status_chip             what may be done with an item
    confidence_meter        evidence strength, as three segments
    score_meter             a deterministic score on a fixed track
    technical_drawer        everything technical, behind one disclosure
    empty_state             an honest nothing-here

Nothing here knows what a readiness state is. Components take labels and tones
the view model has already decided, which is what keeps presentation rules in
one place and out of the markup.
"""

import html as _html
import re as _re


#: The five tones a component may carry. A tone is a *meaning*, not a colour:
#: ``ready`` is the only one that takes the accent, and ``waiting`` is a warm
#: neutral rather than red, because "not yet known" is not a failure.
TONES = ("ready", "waiting", "idea", "blocked", "off")

#: Structural tokens. The brand contributes three more (see ``theme.Theme``).
TOKENS = {
    # ---- ground and ink -------------------------------------------------
    #: The page is the warm ground; a card is plain white on top of it. The gap
    #: between the two is what makes a module read as a module from across the
    #: room, so it is a real step rather than the hairline it used to be.
    "--td-page": "#f4f2ed",
    "--td-surface": "#ffffff",
    "--td-surface-sunk": "#efece5",
    #: A half-step between the page and a card: warm, barely there, and what a
    #: quieter module sits on so it reads as secondary without a rule saying so.
    "--td-surface-warm": "#faf8f4",
    "--td-ink": "#1b1c1a",
    "--td-ink-soft": "#55574f",
    "--td-ink-faint": "#8d8f86",
    "--td-rule": "#ded9d0",
    "--td-rule-soft": "#e9e5dc",
    # ---- status, all desaturated ---------------------------------------
    "--td-wait": "#8a6a35",
    "--td-wait-soft": "#f6f1e6",
    "--td-idea": "#4f5361",
    "--td-idea-soft": "#eeeff2",
    "--td-stop": "#94453b",
    "--td-stop-soft": "#f7ece9",
    "--td-off": "#9a9c93",
    "--td-off-soft": "#f0efea",
    # ---- type ------------------------------------------------------------
    #: Headings, and the large figures that behave like headings. Belanosima
    #: travels inside the page (see ``typeface``), so the fallbacks exist for
    #: the case where a reader has disabled embedded fonts entirely — a serif
    #: stack, because that is what these headings were set in before and it
    #: keeps the fallback page recognisably the same document.
    "--td-display": ('"Belanosima", ui-serif, Georgia, "Iowan Old Style", '
                     '"Palatino Linotype", serif'),
    #: Large FIGURES, which are not headings and are read differently. Belanosima
    #: draws a perfect-circle zero with no slash, and a lone 0 above "Ready to
    #: act on now" reads as the letter O — a legibility cost a metric band
    #: cannot carry. The figures keep the serif they already had: tabular,
    #: unambiguous, and a deliberate second voice for data against the heading's.
    "--td-figure": ('ui-serif, Georgia, "Iowan Old Style", "Palatino Linotype", '
                    '"Times New Roman", serif'),
    "--td-sans": ('-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, '
                  '"Helvetica Neue", Arial, sans-serif'),
    "--td-mono": ('ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, '
                  "monospace"),
    # ---- rhythm ----------------------------------------------------------
    "--td-measure": "68rem",
    "--td-section": "4rem",
    #: Air BETWEEN modules, on top of the padding inside them. Separating the
    #: two means a section can breathe more without its own header drifting
    #: away from the content it labels.
    "--td-section-gap": "1.25rem",
    "--td-radius": "5px",
    #: Two layers, both warm-black rather than blue, and both weak enough that
    #: the card still sits ON the page rather than above it: a one-pixel
    #: contact edge, and a wide, very light spread that reads as air.
    "--td-shadow": ("0 1px 1px rgba(43, 38, 28, .04), "
                    "0 6px 16px -8px rgba(43, 38, 28, .10)"),
    #: For modules that are deliberately quieter than the decisions above them.
    "--td-shadow-soft": "0 1px 2px rgba(43, 38, 28, .04)",
}


def escape(value):
    return _html.escape("" if value is None else str(value), quote=True)


def tone_class(name):
    return name if name in TONES else "waiting"


def _token_block(theme):
    values = dict(TOKENS)
    values.update(theme.tokens())
    body = "\n".join(f"  {name}: {value};" for name, value in sorted(values.items()))
    return ":root {\n" + body + "\n}"


STYLESHEET = """
*, *::before, *::after { box-sizing: border-box; }

html { -webkit-text-size-adjust: 100%; }

body {
  margin: 0;
  background: var(--td-page);
  color: var(--td-ink);
  font-family: var(--td-sans);
  font-size: 16px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.td-wrap { max-width: var(--td-measure); margin: 0 auto; padding: 0 2.5rem; }

/* ---------------------------------------------------------------- type -- */

.td-eyebrow {
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--td-ink-faint);
  margin: 0;
}

/* Belanosima is a geometric sans where a serif used to be, and it carries more
   optical weight at the same measurement. So every heading below is set a
   little smaller and a little tighter than the serif was: the hierarchy is
   unchanged, the presence is the same, and the page does not start shouting. */

.td-title {
  font-family: var(--td-display);
  font-weight: 400;
  font-size: clamp(1.875rem, 3.9vw, 2.625rem);
  line-height: 1.12;
  letter-spacing: -0.025em;
  margin: 1rem 0 0;
}

.td-section-title {
  font-family: var(--td-display);
  font-weight: 400;
  font-size: 1.4375rem;
  line-height: 1.25;
  letter-spacing: -0.02em;
  margin: 0.625rem 0 0;
}

.td-lede { color: var(--td-ink-soft); margin: 0.5rem 0 0; max-width: 60ch; }

/* -------------------------------------------------------------- header -- */

.td-header { padding: 3.5rem 0 2.25rem; }

.td-wordmark {
  display: flex; align-items: center; gap: 0.75rem;
  font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.2em;
  text-transform: uppercase; color: var(--td-ink-soft); margin: 0;
}

.td-wordmark::before {
  content: ""; width: 1.75rem; height: 2px;
  background: var(--td-accent); flex: none;
}

.td-facts {
  display: flex; flex-wrap: wrap; gap: 0.5rem 2rem;
  margin: 1.5rem 0 0; padding: 0; list-style: none;
  font-size: 0.8125rem; color: var(--td-ink-faint);
}

.td-facts b { color: var(--td-ink-soft); font-weight: 600; }

/* The brand mark, when one is installed. Height-constrained rather than
   width-constrained: a wordmark and a square mark should sit on the same
   baseline whatever their aspect ratio. */
.td-wordmark--mark { gap: 0.875rem; }
.td-wordmark--mark::before { display: none; }

.td-wordmark img {
  height: 1.75rem; width: auto; max-width: 12rem; display: block;
}

.td-wordmark--mark span {
  padding-left: 0.875rem; border-left: 1px solid var(--td-rule);
}

/* -------------------------------------------------------- report nav -- */

/* One row, and it SCROLLS rather than wraps. A second line of tabs reads as a
   second navigation, and on a phone a wrapped seven-item grid is the thing
   that makes a considered report look assembled. The fades at the edges are
   the only affordance that says there is more to the right — a scrollbar on a
   client report is furniture nobody wants to see. */

.td-nav {
  position: relative;
  border-top: 1px solid var(--td-rule-soft);
  border-bottom: 1px solid var(--td-rule);
  margin: 1.75rem 0 0;
}

.td-nav-scroll {
  display: flex; gap: 0.25rem; overflow-x: auto; scrollbar-width: none;
  -webkit-overflow-scrolling: touch; scroll-snap-type: x proximity;
}

.td-nav-scroll::-webkit-scrollbar { display: none; }

.td-nav a, .td-nav span {
  flex: none; scroll-snap-align: start;
  padding: 0.9375rem 1.0625rem 0.8125rem;
  font-size: 0.8125rem; font-weight: 600; letter-spacing: 0.015em;
  white-space: nowrap; text-decoration: none;
  border-bottom: 2px solid transparent;
  border-radius: var(--td-radius) var(--td-radius) 0 0;
  margin-bottom: -1px;
  transition: background-color .15s ease, color .15s ease;
}

/* A tab should answer "can I click this?" before it is clicked. A warm wash on
   hover is enough; a border or a shadow here would make the bar a component in
   its own right, and it is meant to sit under the masthead quietly. */
.td-nav a { color: var(--td-ink-soft); }
.td-nav a:hover {
  color: var(--td-ink); background: var(--td-surface-warm);
  border-bottom-color: var(--td-rule);
}
.td-nav a:focus-visible {
  outline: 2px solid var(--td-accent); outline-offset: -2px;
}

/* The active report. The accent is spent here and nowhere else in this bar. */
.td-nav a[aria-current="page"] {
  color: var(--td-ink); border-bottom-color: var(--td-accent);
}

/* Not connected yet: present, so the reader can see the shape of the whole
   programme, and plainly not a link. Muted rather than struck through or
   badged — a row of "soon" pills is noise, and this says the same thing. */
.td-nav span {
  color: var(--td-off); cursor: default;
}

.td-nav-note {
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0;
}

/* ---------------------------------------------------------- conclusion -- */

.td-conclusion {
  background: var(--td-surface);
  border: 1px solid var(--td-rule);
  border-radius: var(--td-radius);
  box-shadow: var(--td-shadow);
  padding: 2.5rem 2.75rem 2.25rem;
}

.td-conclusion-top {
  display: flex; flex-wrap: wrap; align-items: center;
  justify-content: space-between; gap: 1rem;
  padding: 0 0 1.5rem; border-bottom: 1px solid var(--td-rule-soft);
}

/* The week's finding, and the one place a long sentence is set large. It is
   PROSE, not a heading: three lines of a rounded display face read as a poster,
   which is the opposite of what a report wants at the moment it states its
   conclusion. So it stays in the body face, sized up and given room. */
.td-conclusion-statement {
  font-family: var(--td-sans);
  font-size: clamp(1.3125rem, 2.4vw, 1.625rem);
  font-weight: 400;
  line-height: 1.45; letter-spacing: -0.012em;
  margin: 1.75rem 0 0; max-width: 46ch; color: var(--td-ink);
}

.td-directives {
  display: grid; gap: 1.75rem 3rem; margin: 2rem 0 0;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
}

.td-directive dt {
  font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--td-ink-faint); margin: 0 0 0.5rem;
  padding: 0 0 0.5rem; border-bottom: 1px solid var(--td-rule-soft);
}

.td-directive dd { margin: 0; color: var(--td-ink-soft); max-width: 42ch; }

.td-directive--focus dt { color: var(--td-accent-ink); }

/* ------------------------------------------------------------- metrics -- */

/* The hairline mesh is drawn by the CELLS, not by a coloured ground showing
   through the gaps. A band holds however many figures a report has, and with
   the ground doing the work the last row's unused cells showed up as grey
   rectangles — furniture that says "missing" about nothing at all. Outlines
   overlap into a single line and take no space, so the mesh is unchanged and
   an empty cell is simply empty. */
.td-metrics {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
  gap: 0; margin: 1.25rem 0 0;
  background: var(--td-surface); border: 1px solid var(--td-rule);
  border-radius: var(--td-radius); overflow: hidden;
  box-shadow: var(--td-shadow);
}

.td-metric {
  background: var(--td-surface); padding: 1.5rem 1.5rem 1.25rem;
  outline: 1px solid var(--td-rule);
}

.td-metric-value {
  font-family: var(--td-figure); font-size: 2.5rem; line-height: 1;
  font-variant-numeric: tabular-nums; margin: 0; letter-spacing: -0.02em;
}

.td-metric--muted .td-metric-value { color: var(--td-ink-faint); }

.td-metric-label {
  font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--td-ink-faint); margin: 0.875rem 0 0;
}

.td-metric-note {
  font-size: 0.8125rem; color: var(--td-ink-soft); margin: 0.375rem 0 0;
}

/* Direction, not judgement: down is not red, because whether down is bad
   depends on the metric and this component does not know which one it holds. */
.td-metric-change {
  font-size: 0.8125rem; font-weight: 600; margin: 0.5rem 0 0;
  color: var(--td-ink-soft);
}

.td-metric-change--up { color: var(--td-accent-ink); }
.td-metric-change--down { color: var(--td-wait); }
.td-metric-change--unknown { color: var(--td-ink-faint); font-weight: 400; }

.td-metric .td-sparkline { display: block; margin: 0.75rem 0 0; color: var(--td-rule); }
.td-metric--trend .td-sparkline { color: var(--td-accent); }

/* --------------------------------------------------------------- tables -- */

.td-table-wrap {
  overflow-x: auto; border: 1px solid var(--td-rule);
  border-radius: var(--td-radius); background: var(--td-surface);
  box-shadow: var(--td-shadow);
}

.td-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }

.td-table caption {
  text-align: left; padding: 1.125rem 1.25rem 0;
  font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--td-ink-faint);
}

.td-table th, .td-table td {
  text-align: left; padding: 0.75rem 1.25rem;
  border-bottom: 1px solid var(--td-rule-soft);
}

.td-table thead th {
  font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--td-ink-faint);
  border-bottom-color: var(--td-rule);
}

.td-table tbody tr:last-child td { border-bottom: 0; }
.td-table td { color: var(--td-ink-soft); }
.td-table .td-numeric {
  text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap;
}
.td-table tbody .td-numeric { color: var(--td-ink); }

/* ------------------------------------------------------------ sparkline -- */

.td-sparkline { display: inline-block; line-height: 0; color: var(--td-ink-faint); }
.td-sparkline svg { width: 100%; height: auto; max-width: 100%; }

/* ---------------------------------------------------------------- note -- */

.td-note {
  background: var(--td-surface-sunk); border-radius: var(--td-radius);
  padding: 1.25rem 1.5rem; border-left: 2px solid var(--td-rule);
  box-shadow: inset 0 1px 2px rgba(43, 38, 28, .03);
}

.td-note p {
  margin: 0.5rem 0 0; color: var(--td-ink-soft); font-size: 0.875rem;
  max-width: 78ch;
}

.td-note .td-eyebrow { margin: 0; }

/* ------------------------------------------------------------ sections -- */

/* Each section is a MODULE, and the eye should find its edges without being
   shown a box. Three quiet things do that: a hairline where one module ends,
   more air than a paragraph break, and a header band that belongs to the
   section rather than floating above it. */

.td-section {
  padding: var(--td-section) 0 0;
  margin: var(--td-section-gap) 0 0;
  border-top: 1px solid var(--td-rule-soft);
}

/* The first section after the conclusion needs no rule: the card above it is
   already an edge, and two edges in a row reads as a mistake. */
.td-section:first-of-type { border-top: 0; margin-top: 0; }

.td-section-head {
  margin: 0 0 1.75rem; padding: 0 0 1.125rem;
  border-bottom: 1px solid var(--td-rule-soft);
}

/* The marker. The same accent tick the masthead wordmark carries, so a section
   label and the brand line are visibly the same system — one restrained mark,
   never an icon set. */
.td-section-head .td-eyebrow {
  display: flex; align-items: center; gap: 0.625rem;
}

.td-section-head .td-eyebrow::before {
  content: ""; width: 1.125rem; height: 2px; flex: none;
  background: var(--td-accent); opacity: 0.55;
}

/* ------------------------------------------------------------ channels -- */

/* Individually bordered rather than a hairline mesh: the channel count is
   whatever a client has declared, and a mesh leaves a ragged empty cell on the
   last row the day that count is not a multiple of the column count. */
.td-channels {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
  gap: 1rem;
}

.td-channel {
  background: var(--td-surface); padding: 1.375rem 1.375rem 1.25rem;
  border: 1px solid var(--td-rule); border-radius: var(--td-radius);
  box-shadow: var(--td-shadow);
  display: flex; flex-direction: column; gap: 0.75rem;
}

/* A channel with nothing to say sits ON the page rather than above it. */
.td-channel--off {
  background: var(--td-surface-warm); border-style: dashed; box-shadow: none;
}

.td-channel-top {
  display: flex; align-items: baseline; justify-content: space-between;
  gap: 0.75rem;
}

.td-channel-name {
  font-size: 0.9375rem; font-weight: 600; margin: 0; line-height: 1.3;
}

.td-channel-top { min-height: 2.4em; }

.td-channel-note {
  font-size: 0.8125rem; line-height: 1.5; color: var(--td-ink-soft);
  margin: 0; max-width: 34ch;
}

.td-channel--off .td-channel-note { color: var(--td-ink-faint); }

.td-channel-figures {
  display: flex; flex-wrap: wrap; gap: 0.25rem 1.5rem; margin: auto 0 0;
  padding: 0.875rem 0 0; border-top: 1px solid var(--td-rule-soft);
}

.td-figure { font-size: 0.8125rem; color: var(--td-ink-faint); }
.td-figure b {
  display: block; font-family: var(--td-figure); font-size: 1.25rem;
  color: var(--td-ink); font-weight: 400; font-variant-numeric: tabular-nums;
}

/* ---------------------------------------------------------- priorities -- */

.td-priorities { border-top: 1px solid var(--td-rule); }

/* The ranked list is one object, not a run of rules across the page: a
   container with its own ground, and hairlines only between the rows inside
   it. The recommended row is tinted rather than outlined — the same trick the
   status chips use, at panel scale. */
.td-priorities {
  background: var(--td-surface); border: 1px solid var(--td-rule);
  border-radius: var(--td-radius); box-shadow: var(--td-shadow);
  overflow: hidden;
}

.td-priority {
  display: grid; gap: 0.375rem 1.75rem; align-items: start;
  grid-template-columns: 3.5rem 1fr auto;
  padding: 1.75rem 1.75rem; border-bottom: 1px solid var(--td-rule-soft);
}

.td-priority:last-child { border-bottom: 0; }
.td-priority--opportunity { background: var(--td-accent-soft); }
.td-priority--monitoring { background: transparent; }

.td-priority-rank {
  font-family: var(--td-figure); font-size: 1.75rem; line-height: 1;
  color: var(--td-rule); font-variant-numeric: tabular-nums;
  grid-row: 1 / span 3;
}

.td-priority--opportunity .td-priority-rank { color: var(--td-accent); }

.td-priority-channel {
  font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--td-ink-faint);
}

.td-priority-title {
  font-family: var(--td-display); font-weight: 400; font-size: 1.25rem;
  line-height: 1.3; margin: 0; letter-spacing: -0.01em;
}

.td-priority-why { color: var(--td-ink-soft); margin: 0; max-width: 58ch; }

.td-priority-state { grid-column: 3; grid-row: 1 / span 2; text-align: right; }

.td-priority-meta {
  grid-column: 3; grid-row: 3; text-align: right;
  display: flex; flex-direction: column; align-items: flex-end; gap: 0.375rem;
}

/* --------------------------------------------------------------- ideas -- */

.td-ideas {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(19rem, 1fr));
  gap: 1.25rem;
}

.td-card--idea {
  border: 1px dashed var(--td-rule); border-radius: var(--td-radius);
  padding: 1.5rem 1.625rem; background: var(--td-surface-warm);
  box-shadow: var(--td-shadow-soft);
}

.td-card--idea h3 {
  font-family: var(--td-display); font-weight: 400; font-size: 1.125rem;
  line-height: 1.3; margin: 0.875rem 0 0;
}

.td-card--idea p {
  font-size: 0.875rem; color: var(--td-ink-soft); margin: 0.625rem 0 0;
}

/* ------------------------------------------------------------- actions -- */

.td-actions {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
  gap: 1px; background: var(--td-rule);
  border: 1px solid var(--td-rule); border-radius: var(--td-radius);
  overflow: hidden; box-shadow: var(--td-shadow);
}

.td-action-group { background: var(--td-surface); padding: 1.75rem 1.625rem; }

.td-action-group h3 {
  font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.14em;
  text-transform: uppercase; margin: 0 0 1rem; color: var(--td-ink-faint);
}

.td-action-group--focus h3 { color: var(--td-accent-ink); }

.td-action-group ul { margin: 0; padding: 0; list-style: none; }

.td-action-group li {
  padding: 0.625rem 0 0.625rem 1rem; position: relative;
  border-top: 1px solid var(--td-rule-soft); color: var(--td-ink-soft);
  font-size: 0.9375rem;
}

.td-action-group li:first-child { border-top: 0; padding-top: 0; }

.td-action-group li::before {
  content: ""; position: absolute; left: 0; top: 1.0625rem;
  width: 4px; height: 4px; border-radius: 50%; background: var(--td-rule);
}

.td-action-group li:first-child::before { top: 0.5rem; }
.td-action-group--focus li::before { background: var(--td-accent); }

.td-action-empty { color: var(--td-ink-faint); font-size: 0.9375rem; margin: 0; }

/* ------------------------------------------------------------ insights -- */

.td-insights {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(17rem, 1fr));
  gap: 1.25rem;
}

.td-insight {
  background: var(--td-surface); border: 1px solid var(--td-rule);
  border-radius: var(--td-radius); padding: 1.5rem 1.625rem;
  box-shadow: var(--td-shadow);
}

.td-insight p { margin: 0.75rem 0 0; color: var(--td-ink-soft); font-size: 0.9375rem; }
.td-insight p:first-of-type { color: var(--td-ink); font-size: 1rem; }

/* --------------------------------------------------------------- chips -- */

.td-chip {
  display: inline-flex; align-items: center; gap: 0.4375rem;
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.02em;
  white-space: nowrap; color: var(--td-ink-soft);
}

.td-chip::before {
  content: ""; width: 0.375rem; height: 0.375rem; border-radius: 50%;
  background: currentColor; flex: none;
}

.td-chip--ready   { color: var(--td-accent-ink); }
.td-chip--waiting { color: var(--td-wait); }
.td-chip--idea    { color: var(--td-idea); }
.td-chip--blocked { color: var(--td-stop); }
.td-chip--off     { color: var(--td-off); }

.td-chip--solid {
  padding: 0.3125rem 0.75rem; border-radius: 999px;
  background: var(--td-off-soft);
}
.td-chip--solid.td-chip--ready   { background: var(--td-accent-soft); }
.td-chip--solid.td-chip--waiting { background: var(--td-wait-soft); }
.td-chip--solid.td-chip--idea    { background: var(--td-idea-soft); }
.td-chip--solid.td-chip--blocked { background: var(--td-stop-soft); }

/* ------------------------------------------------------------- meters -- */

.td-meter {
  display: inline-flex; align-items: center; gap: 0.5rem;
  font-size: 0.75rem; color: var(--td-ink-faint);
}

.td-meter-track { display: inline-flex; gap: 2px; }

.td-meter-track i {
  width: 0.875rem; height: 2px; border-radius: 1px;
  background: var(--td-rule); display: block;
}

.td-meter-track i.on { background: var(--td-ink-faint); }

.td-score { display: inline-flex; align-items: center; gap: 0.5rem;
            font-size: 0.75rem; color: var(--td-ink-faint); }

.td-score-track {
  position: relative; width: 4.5rem; height: 2px; border-radius: 1px;
  background: var(--td-rule); overflow: hidden;
}

.td-score-fill {
  position: absolute; inset: 0 auto 0 0; background: var(--td-ink-faint);
}

.td-priority--opportunity .td-score-fill { background: var(--td-accent); }

.td-score-value { font-variant-numeric: tabular-nums; color: var(--td-ink-soft); }

/* --------------------------------------------------------------- empty -- */

.td-empty {
  border: 1px dashed var(--td-rule); border-radius: var(--td-radius);
  padding: 2rem; color: var(--td-ink-soft); max-width: 60ch;
}

/* -------------------------------------------------------------- onward -- */

/* The only link the system draws, and it is drawn as a destination rather
   than as a button. A report is a document; a button in one implies something
   will happen, and the only thing that happens here is that a different
   document opens. */
.td-onward {
  display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.75rem 1.25rem;
  margin: 1.5rem 0 0;
}
.td-onward a {
  color: var(--td-accent-ink); font-weight: 600; text-decoration: none;
  border-bottom: 1px solid var(--td-accent); padding-bottom: 0.15rem;
}
.td-onward a:hover, .td-onward a:focus { border-bottom-width: 2px; }
.td-onward p {
  margin: 0; color: var(--td-ink-soft); font-size: 0.875rem; max-width: 60ch;
}

/* ---------------------------------------------------------- disclosure -- */

/* The drawer is a module like the others, closed. Same ground, same border,
   same radius — so "there is more here" reads as part of the system rather
   than as a footnote someone appended. */
.td-technical {
  margin: var(--td-section) 0 0;
  background: var(--td-surface-warm);
  border: 1px solid var(--td-rule);
  border-radius: var(--td-radius);
  box-shadow: var(--td-shadow-soft);
  padding: 0.25rem 1.75rem 0.5rem;
}

.td-technical summary {
  cursor: pointer; font-size: 0.6875rem; font-weight: 600;
  letter-spacing: 0.14em; text-transform: uppercase; color: var(--td-ink-faint);
}

.td-technical summary::marker { color: var(--td-rule); }

.td-technical h3 {
  font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--td-ink-faint);
  margin: 2rem 0 0.75rem;
}

.td-technical ul { margin: 0; padding-left: 1.125rem; }

.td-technical li, .td-technical td, .td-technical th {
  font-size: 0.8125rem; color: var(--td-ink-soft); line-height: 1.55;
}

.td-technical table { width: 100%; border-collapse: collapse; margin: 0.5rem 0 0; }

.td-technical th, .td-technical td {
  text-align: left; vertical-align: top; font-weight: 400;
  padding: 0.4375rem 1rem 0.4375rem 0; border-bottom: 1px solid var(--td-rule-soft);
}

.td-technical th { width: 34%; color: var(--td-ink); font-weight: 600; }
.td-technical code { font-family: var(--td-mono); font-size: 0.75rem; word-break: break-all; }

/* -------------------------------------------------------------- footer -- */

.td-footer {
  margin: var(--td-section) 0 0; padding: 1.5rem 0 4rem;
  border-top: 1px solid var(--td-rule); font-size: 0.8125rem;
  color: var(--td-ink-faint);
}

.td-footer p { margin: 0; max-width: 64ch; }

.td-signature { margin: 0 0 1rem !important; }
.td-signature img { height: 1.5rem; width: auto; max-width: 10rem; opacity: 0.7; }

/* -------------------------------------------------------- small screen -- */

@media (max-width: 48rem) {
  .td-wrap { padding: 0 1.25rem; }
  .td-header { padding: 2.5rem 0 1.5rem; }
  .td-nav { margin-top: 1.25rem; }
  .td-nav a, .td-nav span { padding: 0.8125rem 0.75rem 0.6875rem; }
  /* The bar runs to both edges of a phone screen; the wrapper's gutter would
     otherwise clip the first and last tab out of reach. */
  .td-nav-scroll { padding: 0 1.25rem; margin: 0 -1.25rem; }
  .td-section { padding: 2.75rem 0 0; }
  .td-conclusion { padding: 1.75rem 1.5rem; }
  .td-metrics { grid-template-columns: repeat(2, 1fr); }
  .td-metric { padding: 1.25rem; }
  .td-metric-value { font-size: 2rem; }
  .td-channels, .td-actions { grid-template-columns: 1fr; }
  .td-table th, .td-table td { padding: 0.625rem 0.875rem; }
  .td-priority { grid-template-columns: 2.25rem 1fr; }
  .td-priority-state, .td-priority-meta {
    grid-column: 2; grid-row: auto; text-align: left; align-items: flex-start;
  }
}

@media print {
  body { background: #fff; }
  .td-technical { display: none; }
  .td-conclusion, .td-insight, .td-channel, .td-metrics, .td-priorities,
  .td-actions, .td-table-wrap, .td-technical, .td-card--idea {
    box-shadow: none;
  }
  .td-priority, .td-channel, .td-insight { break-inside: avoid; }
}
"""


# --------------------------------------------------------------------------
# Shell
# --------------------------------------------------------------------------

def page(title, body, theme=TRAFFICDOM, lang="en"):
    """The document shell. Self-contained: no external stylesheet, font or script.

    A client report that depends on a CDN renders differently depending on where
    and when it is opened, and quietly tells a third party who opened it.
    """
    return "\n".join([
        "<!DOCTYPE html>",
        f'<html lang="{escape(lang)}">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="robots" content="noindex, nofollow">',
        f"<title>{escape(title)}</title>",
        f"<style>{font_faces()}\n{_token_block(theme)}\n"
        f"{STYLESHEET}</style>",
        "</head>",
        "<body>",
        body,
        "</body>",
        "</html>",
        "",
    ])


def wrap(parts):
    """The measured column every section sits in."""
    return f'<div class="td-wrap">{"".join(part for part in parts if part)}</div>'


# --------------------------------------------------------------------------
# Chips and meters — the small shared vocabulary
# --------------------------------------------------------------------------

def status_chip(label, tone="waiting", solid=False):
    """What may be done with an item, as one unambiguous mark.

    One component for every "may I act on this?" answer in every report, so the
    answer looks the same everywhere and cannot be softened by styling.
    """
    classes = f"td-chip td-chip--{tone_class(tone)}"
    if solid:
        classes += " td-chip--solid"
    return f'<span class="{classes}">{escape(label)}</span>'


def confidence_meter(label, level=0):
    """Evidence strength, as three segments plus its name.

    Segments rather than a percentage: the judgement is ordinal, and rendering
    it as a number would invite arithmetic it cannot support.
    """
    segments = "".join(
        f'<i class="{"on" if index < level else ""}"></i>' for index in range(3))
    return ('<span class="td-meter">'
            f'<span class="td-meter-track">{segments}</span>'
            f"<span>{escape(label)}</span></span>")


def score_meter(score, label="Score", maximum=1.0):
    """A deterministic score on a fixed track — the same scale on every row.

    Deliberately small and grey: the number is secondary to the ranking it
    produced, and a chart that shouted would invert that.
    """
    if score is None:
        return ""
    try:
        fraction = max(0.0, min(1.0, float(score) / float(maximum)))
    except (TypeError, ValueError, ZeroDivisionError):
        return ""
    return ('<span class="td-score">'
            f"<span>{escape(label)}</span>"
            '<span class="td-score-track">'
            f'<span class="td-score-fill" style="width: {fraction * 100:.1f}%"></span>'
            "</span>"
            f'<span class="td-score-value">{escape(score)}</span></span>')


# --------------------------------------------------------------------------
# Header and conclusion
# --------------------------------------------------------------------------

def brand_mark(theme=TRAFFICDOM, wordmark=None):
    """The logo when one is installed, the typographic wordmark otherwise.

    Both are finished designs. The fallback is not a placeholder waiting for an
    asset: a report whose brand mark is a letterspaced line of type is a report
    that still looks deliberate, and one that cannot break because a file is
    missing.
    """
    label = wordmark or theme.wordmark
    if theme.logo:
        return ('<p class="td-wordmark td-wordmark--mark">'
                f'<img src="{escape(theme.logo)}" alt="{escape(theme.logo_alt)}">'
                f"<span>{escape(label)}</span></p>")
    return f'<p class="td-wordmark">{escape(label)}</p>'


def report_header(title, eyebrow=None, facts=(), theme=TRAFFICDOM,
                  wordmark=None, client=None, report=None):
    """Masthead: brand mark, report title, the facts that date it, and the bar.

    ``wordmark`` names which report this is — "Growth Engine", "Weekly
    Analytics" — under the same mark. That is the whole trick to making two
    reports feel like one suite: identical furniture, one line of difference.

    ``client`` and ``report`` add the navigation, inside the masthead where it
    belongs: the tabs are part of the identity of the page, not a widget under
    it. Both are needed or neither — a bar without a client id has no routes to
    offer, and one without a report type cannot say which tab you are on.

    The header takes the two facts and builds the bar itself rather than
    accepting rendered markup, so no report can hand it a different navigation.
    """
    rows = "".join(
        f"<li>{escape(label)} <b>{escape(value)}</b></li>"
        for label, value in facts if value
    )
    return (
        '<header class="td-header">'
        f"{brand_mark(theme, wordmark)}"
        f'<h1 class="td-title">{escape(title)}</h1>'
        + (f'<p class="td-lede">{escape(eyebrow)}</p>' if eyebrow else "")
        + (f'<ul class="td-facts">{rows}</ul>' if rows else "")
        + (report_nav(client, report) if client and report else "")
        + "</header>"
    )


#: Every report in a TrafficDom client suite, in the order the bar shows them.
#:
#: ``key`` is the report's own type — what a renderer calls itself, and what
#: decides which tab is active. ``segment`` is the URL segment beneath the
#: client, and ``None`` means the suite root: Analytics is the report a client
#: lands on, so it lives at ``/reports/<client>/`` rather than one level down.
#:
#: The table is here, in the shared system, for the same reason the components
#: are: two repositories render these reports, and a navigation bar that
#: disagrees with itself between tabs is worse than none. Adding a channel is
#: one edit in one place, and both reports gain the tab on the next export.
REPORTS = (
    ("analytics", None, "Analytics"),
    ("growth", "growth", "Growth"),
    # The segment the Analytics repository's publisher already writes to for
    # this report — `--section email-marketing`, not `email`. The table follows
    # the route that exists rather than the one that reads more tidily: a tab
    # is only worth anything if it lands somewhere.
    ("email", "email-marketing", "Email Marketing"),
    ("social", "social", "Social"),
    ("paid", "paid", "Paid"),
    ("cro", "cro", "CRO"),
    ("retention", "retention", "Retention"),
)

#: Which of them a client can actually open today. Everything else is rendered
#: as present-but-not-connected: a tab that links to a page that does not exist
#: is worse than one that says it is not there yet.
LIVE_REPORTS = ("analytics", "growth", "email")

#: Where a client's reports live. One prefix, joined to a client id at render
#: time — no client name appears anywhere in this system.
REPORT_ROOT = "/reports"

#: A client id safe to put in a path: lowercase, digits, hyphen, underscore.
#: Anything else is refused rather than escaped, because a client id that needs
#: escaping to sit in a URL is a configuration mistake, and a quietly mangled
#: link is harder to notice than a failed render.
_CLIENT_ID = _re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def report_path(client, report):
    """The route for one report of one client.

    ``/reports/<client>/`` for the suite root, ``/reports/<client>/<segment>/``
    for everything else. Trailing slash throughout, because these are
    directories on the report host and a link without one costs a redirect.
    """
    client = str(client or "").strip()
    if not _CLIENT_ID.match(client):
        raise ValueError(
            f"{client!r} is not usable as a client id in a URL. Expected "
            "lowercase letters, digits, hyphen or underscore."
        )
    for key, segment, _label in REPORTS:
        if key == report:
            tail = f"{segment}/" if segment else ""
            return f"{REPORT_ROOT}/{client}/{tail}"
    raise ValueError(f"no such report: {report!r}")


def report_nav(client, active, live=LIVE_REPORTS, reports=REPORTS):
    """The bar that moves a client between their reports.

    One implementation, rendered by every report, so the tabs cannot disagree
    about what exists or what a route is. The caller supplies only which report
    it is; the routes are derived from the client id and the table above.

    ``active`` is the report's own type, so a report cannot mislabel itself by
    passing a URL it guessed. An unknown ``active`` renders the bar with nothing
    marked current rather than raising: a navigation bar is not worth failing a
    client report over.
    """
    tabs = []
    for key, _segment, label in reports:
        if key in live:
            current = ' aria-current="page"' if key == active else ""
            tabs.append(f'<a href="{escape(report_path(client, key))}"'
                        f"{current}>{escape(label)}</a>")
        else:
            # Not a link, and said so twice: muted for the eye, and stated for
            # a screen reader, which cannot see that it is grey.
            tabs.append(f'<span aria-disabled="true" title="Not connected yet">'
                        f'{escape(label)}'
                        f'<i class="td-nav-note"> — not connected yet</i>'
                        "</span>")
    return ('<nav class="td-nav" aria-label="Reports">'
            f'<div class="td-nav-scroll">{"".join(tabs)}</div>'
            "</nav>")


def conclusion_card(status_label, tone, period, statement, directives=()):
    """The week in four sentences: state, conclusion, and what to do about it.

    The size of this component is the argument. A reader who stops here should
    have the correct impression of the week, so there is room for one statement
    and a short list of directives — and no room for anything else.
    """
    entries = "".join(
        f'<div class="td-directive{" td-directive--focus" if emphasis else ""}">'
        f"<dt>{escape(term)}</dt><dd>{escape(value)}</dd></div>"
        for term, value, emphasis in directives if value
    )
    return (
        '<div class="td-conclusion">'
        '<div class="td-conclusion-top">'
        f"{status_chip(status_label, tone, solid=True)}"
        + (f'<p class="td-eyebrow">{escape(period)}</p>' if period else "")
        + "</div>"
        f'<p class="td-conclusion-statement">{escape(statement)}</p>'
        + (f'<dl class="td-directives">{entries}</dl>' if entries else "")
        + "</div>"
    )


def sparkline(points, width=200, height=40, label=None):
    """A trend, drawn small. The only chart in the system, and it earns it.

    A series of numbers is nearly unreadable as text and immediate as a line, so
    this exists — but it carries no axis, no gridlines and no tooltip, because a
    sparkline that grows those has become a chart and belongs in a tool rather
    than a briefing.
    """
    values = [value for value in (points or ()) if isinstance(value, (int, float))]
    if len(values) < 2:
        return ""
    low, high = min(values), max(values)
    span = (high - low) or 1.0
    step = width / (len(values) - 1)
    coordinates = " ".join(
        f"{index * step:.1f},{height - ((value - low) / span) * (height - 4) - 2:.1f}"
        for index, value in enumerate(values)
    )
    return (
        '<span class="td-sparkline">'
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'role="img" aria-label="{escape(label or "trend")}" '
        'preserveAspectRatio="none" focusable="false">'
        f'<polyline points="{coordinates}" fill="none" stroke="currentColor" '
        'stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>'
        "</svg></span>"
    )


#: How a figure moved. ``flat`` is a real answer, not a missing one, and
#: ``unknown`` is the honest state when there is nothing to compare against —
#: which must never render as a zero.
DIRECTIONS = {
    "up": "\u2191", "down": "\u2193", "flat": "\u2192", "unknown": "",
}


def metric(value, label, note=None, muted=False, change=None, direction=None,
           trend=None, trend_label=None):
    """One headline figure, optionally with how it moved.

    The change is the reason the Analytics report exists, so it sits directly
    under the number rather than in a caption. The arrow is a direction, never a
    judgement: down is not styled as bad, because whether down is bad depends on
    the metric and this component does not know which one it is holding.
    """
    classes = "td-metric td-metric--muted" if muted else "td-metric"
    arrow = DIRECTIONS.get(direction or "unknown", "")
    movement = ""
    if change:
        movement = (f'<p class="td-metric-change td-metric-change--'
                    f'{escape(direction or "unknown")}">'
                    + (f'<span aria-hidden="true">{arrow}</span> ' if arrow else "")
                    + f"{escape(change)}</p>")
    line = sparkline(trend, width=180, height=32, label=trend_label) if trend else ""
    if line:
        classes += " td-metric--trend"
    return (
        f'<div class="{classes}">'
        f'<p class="td-metric-value">{escape(value)}</p>'
        f"{movement}"
        f'<p class="td-metric-label">{escape(label)}</p>'
        + (f'<p class="td-metric-note">{escape(note)}</p>' if note else "")
        + line
        + "</div>"
    )


def metric_band(cards):
    """The headline figures, as one hairline-separated row.

    Takes rendered cards, like every other container here — ``channel_grid``,
    ``priority_list``, ``idea_grid``. One convention across the system means a
    report never has to remember which containers build their own children.
    """
    cells = "".join(cards)
    return f'<div class="td-metrics">{cells}</div>' if cells else ""


def section(title, body, eyebrow=None, lede=None, anchor=None):
    """A titled block. The eyebrow labels it; the lede sets expectations.

    ``anchor`` gives the section a stable id, so a report can be linked to by
    part — "see the recommendations" in an email should land on them.
    """
    head = "".join([
        f'<p class="td-eyebrow">{escape(eyebrow)}</p>' if eyebrow else "",
        f'<h2 class="td-section-title">{escape(title)}</h2>',
        f'<p class="td-lede">{escape(lede)}</p>' if lede else "",
    ])
    identity = f' id="{escape(anchor)}"' if anchor else ""
    return (f'<section class="td-section"{identity}>'
            f'<div class="td-section-head">{head}</div>{body}</section>')


# --------------------------------------------------------------------------
# Channels
# --------------------------------------------------------------------------

def channel_card(name, state_label, tone, observation=None, figures=()):
    """One channel's health: state, one sentence, and at most a figure or two.

    No gap lists and no technical detail. The question a reader has here is
    "can this report see my email programme?", and that is answered by a state
    and a sentence.
    """
    stats = "".join(
        f'<span class="td-figure"><b>{escape(value)}</b>{escape(label)}</span>'
        for label, value in figures if value not in (None, "")
    )
    classes = "td-channel td-channel--off" if tone == "off" else "td-channel"
    return (
        f'<div class="{classes}">'
        '<div class="td-channel-top">'
        f'<h3 class="td-channel-name">{escape(name)}</h3>'
        f"{status_chip(state_label, tone)}"
        "</div>"
        + (f'<p class="td-channel-note">{escape(observation)}</p>'
           if observation else "")
        + (f'<div class="td-channel-figures">{stats}</div>' if stats else "")
        + "</div>"
    )


def channel_grid(cards):
    return f'<div class="td-channels">{"".join(cards)}</div>' if cards else ""


# --------------------------------------------------------------------------
# Priorities, ideas, actions, insights
# --------------------------------------------------------------------------

def priority_row(rank, channel, title, why, state_label, tone,
                 recommended=False, priority_label=None, score=None,
                 confidence_label=None, confidence_level=0):
    """One ranked opportunity — the unit this section is scanned by.

    ``recommended`` is the only thing that changes the row's class, and the view
    model refuses to set it under a closed gate. So a withheld item cannot be
    styled as an approved action; it is a different row, not the same row with a
    softer adjective.
    """
    kind = "opportunity" if recommended else "monitoring"
    meta = "".join(part for part in (
        score_meter(score),
        confidence_meter(confidence_label, confidence_level)
        if confidence_label else "",
    ) if part)
    return (
        f'<article class="td-priority td-priority--{kind} td-card--{kind}">'
        f'<div class="td-priority-rank">{escape(rank)}</div>'
        f'<div class="td-priority-channel">{escape(channel)}</div>'
        f'<h3 class="td-priority-title">{escape(title)}</h3>'
        f'<p class="td-priority-why">{escape(why)}</p>'
        '<div class="td-priority-state">'
        f"{status_chip(state_label, tone, solid=True)}"
        + (f"<br>{status_chip(priority_label, 'off')}" if priority_label else "")
        + "</div>"
        + (f'<div class="td-priority-meta">{meta}</div>' if meta else "")
        + "</article>"
    )


def priority_list(rows):
    return f'<div class="td-priorities">{"".join(rows)}</div>' if rows else ""


def idea_card(title, statement, state_label, tone="idea"):
    """An exploratory idea. No score, no priority, no confidence.

    Those fields are absent because the thing itself lacks them, and an empty
    field invites a reader to fill it in. The dashed outline does real work: it
    says at a glance that this is not a finding.
    """
    return (
        '<article class="td-card--idea">'
        f"{status_chip(state_label, tone)}"
        f"<h3>{escape(title)}</h3>"
        f"<p>{escape(statement)}</p>"
        "</article>"
    )


def idea_grid(cards):
    return f'<div class="td-ideas">{"".join(cards)}</div>' if cards else ""


def action_group(title, items, emphasis=False, empty="Nothing in this group."):
    """One of the three answers to "what do we do on Monday?"."""
    classes = "td-action-group td-action-group--focus" if emphasis \
        else "td-action-group"
    if items:
        body = "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"
    else:
        body = f'<p class="td-action-empty">{escape(empty)}</p>'
    return f'<div class="{classes}"><h3>{escape(title)}</h3>{body}</div>'


def action_columns(groups):
    return f'<div class="td-actions">{"".join(groups)}</div>' if groups else ""


def insight_card(headline, detail=None):
    """One short learning. Two sentences at most, by construction."""
    return (
        '<article class="td-insight">'
        f'<p>{escape(headline)}</p>'
        + (f"<p>{escape(detail)}</p>" if detail else "")
        + "</article>"
    )


def insight_grid(cards):
    return f'<div class="td-insights">{"".join(cards)}</div>' if cards else ""


def data_table(columns, rows, caption=None):
    """A ranked list of entities — top pages, top queries, top anything.

    Deliberately plain: hairlines, tabular numerals, no zebra striping and no
    borders around cells. A table earns its place when the reader wants to
    compare rows, and everything else in it is noise.
    """
    if not rows:
        return ""
    numeric_class = ' class="td-numeric"'
    head = "".join(
        f"<th{numeric_class if numeric else ''}>{escape(name)}</th>"
        for name, numeric in columns
    )
    body = "".join(
        "<tr>" + "".join(
            f"<td{numeric_class if numeric else ''}>{escape(cell)}</td>"
            for cell, (_, numeric) in zip(row, columns)
        ) + "</tr>"
        for row in rows
    )
    return (
        '<div class="td-table-wrap"><table class="td-table">'
        + (f"<caption>{escape(caption)}</caption>" if caption else "")
        + f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"
    )


def note_panel(title, body):
    """A short explanation that qualifies the figures above it.

    Sunk rather than raised: it is context, not a finding, and a caveat styled
    like a card competes with the results it is qualifying.
    """
    if not body:
        return ""
    return ('<div class="td-note">'
            + (f'<h3 class="td-eyebrow">{escape(title)}</h3>' if title else "")
            + f"<p>{escape(body)}</p></div>")


def empty_state(text):
    """An honest nothing-here. Says why, so it does not read as a failure."""
    return f'<div class="td-empty">{escape(text)}</div>'


def onward_link(label, href, note=None):
    """A link to the report that continues this one.

    The only link component in the system, and deliberately not a button. A
    button promises that something will happen; the only thing that happens
    here is that another document opens, and a summary card that looked
    clickable-into-an-action would be making a promise the page cannot keep.

    ``href`` is escaped like any other value. A report's own composition
    supplies it, never a document — a URL that arrived inside an artifact would
    be untrusted input pointing wherever it liked.
    """
    if not (label or "").strip() or not (href or "").strip():
        return ""
    return ('<div class="td-onward">'
            f'<a href="{escape(href)}">{escape(label)}</a>'
            + (f"<p>{escape(note)}</p>" if note else "")
            + "</div>")


# --------------------------------------------------------------------------
# The drawer
# --------------------------------------------------------------------------

def technical_drawer(blocks, summary="Technical evidence"):
    """Everything technical, behind one disclosure the reader must open.

    Nothing is removed — the internal states, the fingerprints, the full gap
    lists and the refusals are all the audit trail, and someone will need them.
    Fencing them here is what lets the report above be written in business
    language while the exact machine state stays recoverable, and lets a test
    check the first claim by scanning everything outside this block.
    """
    body = "".join(part for part in blocks if part)
    if not body:
        return ""
    return ('<details class="td-technical">'
            f"<summary>{escape(summary)}</summary>{body}</details>")


def technical_table(title, rows):
    body = "".join(
        f"<tr><th>{escape(term)}</th><td><code>{escape(value)}</code></td></tr>"
        for term, value in rows if value not in (None, "", [], {})
    )
    if not body:
        return ""
    return f"<h3>{escape(title)}</h3><table><tbody>{body}</tbody></table>"


def technical_list(title, items):
    entries = "".join(f"<li>{escape(item)}</li>" for item in items if item)
    if not entries:
        return ""
    return f"<h3>{escape(title)}</h3><ul>{entries}</ul>"


def footer(theme=TRAFFICDOM, statement=None):
    """The standing statement, under the brand signature."""
    signature = ""
    if theme.logo:
        signature = ('<p class="td-signature">'
                     f'<img src="{escape(theme.logo)}" '
                     f'alt="{escape(theme.logo_alt)}"></p>')
    return ('<footer class="td-footer">'
            f"{signature}<p>{escape(statement or theme.footer)}</p></footer>")


# --- integrity ---
# sha256 of every byte above this marker, first 16 hex characters. A consumer
# splits on the marker, hashes what precedes it, and compares — needing to know
# nothing about how this file was assembled.
CONTENT_HASH = "a2c6057fb819dc21"
