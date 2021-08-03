<!-- Tested with xalan-j_2_7_1-bin.zip, Xerces-J-bin.2.11.0.tar.gz on
     OpenJDK 1.7.0_15

    $ LC_ALL=C java -cp xalan.jar:serializer.jar:xercesImpl.jar:xml-apis.jar \
      org.apache.xalan.xslt.Process -in simple.xml -xsl xalan_write.xsl
-->
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:redirect="http://xml.apache.org/xalan/redirect"
    extension-element-prefixes="redirect">
  <xsl:output omit-xml-declaration="yes" indent="yes"/>
  <xsl:template match="/">
    <redirect:write file="xalan_redirect.txt" method="text">
      <xsl:text>Something bad happens here!&#13;</xsl:text>
    </redirect:write>
  </xsl:template>
</xsl:stylesheet>

